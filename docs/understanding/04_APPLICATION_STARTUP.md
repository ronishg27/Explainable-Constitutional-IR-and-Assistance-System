# Application Startup

## Entry Point

```
python backend/app.py
```

The true entry point is `main()` at `backend/app.py:31`. Python executes module-level code as it loads `app.py`, then calls `main()` via the `if __name__ == "__main__"` guard at line 48.

---

## Step-by-Step Startup Trace

### 0. Module Import Phase (Python interpreter, during import of `app.py`)

Before `main()` runs, importing `app.py` resolves all top-level imports. This triggers a cascade:

| File Loaded | Side Effect | Objects Created |
|-------------|-------------|-----------------|
| `app.py` | Imports downstream modules | None |
| `config/log_config.py` | Imports logging + flask | `ContextFilter` class defined |
| `config/db_connect.py` | Imports mongoengine | `Database` class defined |
| `services/qa_service.py` | Imports `engine_factory`, `reranker`, `retrieval_workflow`, `rag_repository`, `rag_workflow`, `rag_formatter`, `article_service`, `message_service` | Module-level `_workflow = None` (line 20) |
| `routes/api_routes.py` | Imports controller functions | **`api_bp = Blueprint("api", __name__)`** — Flask Blueprint object created at line 16 |
| `routes/auth_routes.py` | Imports controller functions | **`auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")`** — line 5 |
| `controllers/api_controller.py` | Imports QAService, MessageService | Controller function objects defined |
| `controllers/auth_controller.py` | Imports UserService, User, RoleEnum | Controller function objects defined |
| `controllers/decorators.py` | Imports jwt, User | `token_required` decorator function defined |
| `models/*.py` | Define mongoengine Document classes | `User`, `Message`, `ReferencedArticle` classes; connection NOT yet open |
| `src/core/*.py` | Define pure algorithm classes | Class objects only; no pipeline assembled yet |
| `src/constants/*.py` | Define data dicts | `CONTRACTIONS_MAP` (57 entries), `STOPWORDS` (~120 words) |

**Key point:** Only class/function/Blueprint objects exist at this point. No database connection, no pipeline, no inference engine.

---

### 1. `load_dotenv(".env", override=True)` — `app.py:32`

```
File:   backend/app.py, line 32
Config: backend/.env (loaded by python-dotenv)
```

- Reads `backend/.env` into `os.environ` with `override=True` (file values win over existing env vars)
- Makes these variables available:
  - `OLLAMA_HOST` (default: `http://127.0.0.1:11434`)
  - `OLLAMA_API_KEY` (optional)
  - `OLLAMA_MODEL` (default: `qwen3:8b`)
  - `MONGO_URI` (default: `mongodb://localhost:27017`)
  - `MONGO_DB_NAME` (default: `ECIRAS`)
  - `JWT_SECRET` (required for auth)

**Why:** Applications needs environment variables before any initialization that depends on them (MongoDB connection string, model names, etc.).

---

### 2. `setup_logging()` — `app.py:33`

```
File: backend/config/log_config.py, line 25
```

- Creates `logs/` directory (via `os.makedirs(log_dir, exist_ok=True)`)
- Creates a **console handler** at `INFO` level
- Creates a **rotating file handler** at `DEBUG` level, writing to `logs/backend.log` (10 MB per file, 5 backups)
- Both handlers use a custom `ContextFilter` that injects HTTP method + route into log records (empty `SYSTEM` / `-` during startup)
- Sets the **root logger** to `DEBUG` so all child loggers inherit

**Why:** Must be early so that all subsequent log statements (`logger.info(...)`, `logger.warning(...)`) have a destination.

**Objects created:**
- `logging.StreamHandler` (console)
- `logging.handlers.RotatingFileHandler` (file)
- `ContextFilter` instances (2 — one per handler)

---

### 3. `init_workflow()` — `app.py:34`

```
File: backend/services/qa_service.py, line 23
```

This is the most complex step. It assembles the entire RAG pipeline and stores it in the module-global `_workflow` variable.

#### 3a. `EngineFactory.from_artifacts(...)` — `qa_service.py:25`

```
File: backend/src/core/engine_factory.py, line 42
Data:  data/output/flattened_nepal_constitution.json
       data/output/tf_index.json
       data/output/pos_index.json
       data/output/doc_stats.json
       data/synonyms.json
```

Step-by-step inside this call:

1. **Load flattened documents** — `engine_factory.py:66-67`
   - Reads `data/output/flattened_nepal_constitution.json` (~700 documents)
   - Converts each dict to a `Document` dataclass (`src/core/document.py`)

2. **Load pre-computed indexes** — `engine_factory.py:69-81`
   - `tf_index.json` — term → doc_id → term frequency
   - `pos_index.json` — term → doc_id → list of positions
   - `doc_stats.json` — `{doc_lengths: {...}, avgdl: float}`
   - These are the outputs of the offline ingestion pipeline (run separately via `python -m preprocessing_scripts.run_ingestion`)

3. **Create two TextProcessors** — `engine_factory.py:86-87`

   | Variable | Lemmatization | Stopwords | Purpose |
   |----------|:-------------:|:---------:|---------|
   | `bm25_proc` | ON | REMOVED | BM25 scoring + candidate generation |
   | `prox_proc` | OFF | KEPT | Proximity pair matching |

   Note: At this point TextProcessor objects are created but **not yet** initialized with spaCy (that happens lazily on first `process_text()` call via `_get_nlp()`).

4. **Load synonym expander** (optional) — `engine_factory.py:89-91`
   - If `synonyms_path` is provided (it is — `data/synonyms.json`), creates `QueryExpander`
   - Constructor loads and parses 44 synonym groups, builds a lookup dict

5. **Create scorers** — `engine_factory.py:93-94`
   - `BM25Scorer(tf_index, doc_lengths, avgdl)` — stores indexes, `N = len(doc_lengths)`
   - `ProximityScorer(pos_index)` — stores positional index

6. **Create SearchEngine** — `engine_factory.py:96-105`
   - Constructor pre-tokenizes all document titles via `bm25_processor.process_text(doc.title)` for fast title-boost lookups (line 76 of `search_engine.py`)
   - This is the **first real work** that happens at startup: ~700 titles are lemmatized via spaCy

**Objects created:**
- `list[Document]` — ~700 dataclass instances
- `dict` tf_index, pos_index, doc_stats — loaded from JSON
- `TextProcessor` × 2
- `QueryExpander`
- `BM25Scorer`
- `ProximityScorer`
- `SearchEngine`

#### 3b. `Reranker(engine.bm25_scorer.tf_index)` — `qa_service.py:29`

```
File: backend/src/core/reranker.py, line 13
```

- Stores the BM25 `tf_index` for later use in RRF fusion and MMR cosine similarity
- Creates an empty `_vector_cache` dict (populated lazily on first `rerank()` call)

**Reason:** The Reranker needs the tf_index to build sparse TF vectors for MMR diversity calculations.

#### 3c. `RetrievalWorkflow(engine, reranker)` — `qa_service.py:30`

```
File: backend/src/workflows/retrieval_workflow.py, line 5
```

- Wires `SearchEngine` + `Reranker` into a single `retrieve()` method
- Sets `default_recall_k = 50`, `default_top_k = 8`

**Reason:** A workflow that composes the two pipeline stages (search → rerank). This is the unit of work used by both the RAG pipeline and any future retrieval-only path.

#### 3d. `RAGRepository(retrieval_workflow)` — `qa_service.py:31`

```
File: backend/src/llm/rag_repository.py, line 40
```

Constructor does:

1. **Stores the retrieval workflow** — `rag_repository.py:46`
2. **Reads model name** — `rag_repository.py:47`
   - `OLLAMA_MODEL` env var or falls back to `"qwen3:8b"`
3. **Creates Ollama client** — `rag_repository.py:49-52`
   - Reads `OLLAMA_HOST` (default `http://127.0.0.1:11434`)
   - Reads `OLLAMA_API_KEY` (optional; sets Bearer header if present)
   - Creates `ollama.Client(host, headers)`
   - **Note:** This just creates the client object — no actual HTTP request yet
4. **Initializes connectivity cache** — `rag_repository.py:54-56`
   - `_ollama_available = None` (lazy — first request will check)
5. **Builds article lookup** — `rag_repository.py:60`
   - `_build_article_lookup()` iterates all ~700 documents and groups them by `article_no`
   - For each article number:
     - If an article-level Document exists (e.g., articles with lettered sub_clauses) → use its text directly
     - If only clause/sub-clause Documents exist → concatenate all clause texts with `\n---\n`
   - Also tracks clause structure per article for later context truncation

**Objects created:**
- `ollama.Client`
- `dict` `_article_lookup` — ~200 article entries (depends on corpus)
- `dict` `_clause_structure` — subset of articles that have clause-level docs

#### 3e. `RAGFormatter()` — `qa_service.py:32`

```
File: backend/src/llm/rag_formatter.py, line 1
```

- Stateless formatter object with three pure methods: `format_context()`, `build_system_prompt()`, `build_user_prompt()`
- No initialization work needed

#### 3f. `RAGWorkflow(repository, formatter)` — `qa_service.py:32`

```
File: backend/src/llm/rag_workflow.py, line 23
```

- Stores the `RAGRepository` and `RAGFormatter`
- Sets `max_context_articles = 8`
- Assigned to module-global `_workflow` at `qa_service.py:20`

```python
_workflow: Optional[RAGWorkflow] = None   # line 20
...
_workflow = RAGWorkflow(repository, RAGFormatter())  # line 32
```

**Why:** Eager initialization means every HTTP request gets predictable response times — no slow first request, no locking, no singleton pattern. The ~1s startup cost is paid once at boot.

---

### 4. `get_spacy_pipeline()` — `app.py:35`

```
File: backend/src/core/text_processor.py, line 8
```

- This function is called **again** here (it was already called during `init_workflow()` when the first `process_text()` ran on ~700 titles)
- The second call hits the `if _spacy_nlp is None` guard and returns the existing cached pipeline
- If this were the first call:
  1. Tries `spacy.load("en_core_web_sm")` — the full English pipeline
  2. Falls back to `spacy.blank("en")` if the model is not installed (tokenization works, lemmas are identity)

**Objects created:** (only on first call)
- `spacy.Language` pipeline (either `en_core_web_sm` or blank `en`)

---

### 5. `create_app()` — `app.py:37`

```
File: backend/app.py, line 19
```

#### 5a. `Flask(__name__)` — `app.py:20`

Creates the Flask WSGI application instance. No special configuration (no secret key, no template folder — it's an API-only app).

**Objects created:**
- `Flask` app instance

#### 5b. `CORS(app, supports_credentials=True)` — `app.py:21`

Wraps the Flask app with CORS middleware. `supports_credentials=True` allows cookies (used as JWT fallback).

**Note:** No origin restrictions are configured — `CORS(app)` with defaults means all origins are allowed. This is technical debt (flagged in `docs/PROJECT_DOCUMENTATION.md`).

#### 5c. `Database().connect(...)` — `app.py:22-25`

```
File: backend/config/db_connect.py, line 15
Config: MONGO_DB_NAME (default "ECIRAS"), MONGO_URI (default "mongodb://localhost:27017")
```

Singleton pattern:

```python
class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

- `Database()` returns the singleton instance
- `.connect()` calls `mongoengine.connect(host, db, alias="default", ...)`
  - `maxPoolSize=10`
  - `minPoolSize=2`
  - `connectTimeoutMS=5000`
  - `serverSelectionTimeoutMS=5000`
- This establishes the connection pool to MongoDB
- **Fail-fast:** If MongoDB is unreachable, an exception is raised and the server will not start

**Objects created:**
- `Database` singleton (once, on first instantiation)
- mongoengine connection pool to `ECIRAS` database

#### 5d. `app.register_blueprint(api_bp)` — `app.py:26`

```
File: backend/routes/api_routes.py, line 16
```

Registers 8 routes under the Flask app:

| Method | Path | Auth | Decorator chain |
|--------|------|:----:|-----------------|
| GET | `/api/v1` | No | `home_route()` → `home()` |
| GET | `/api/v1/health` | No | `health_route()` → `health()` |
| POST | `/api/v1/ask` | JWT | `@token_required` → `ask_route()` → `ask()` |
| POST | `/api/v1/ask-stream` | JWT | `@token_required` → `ask_stream_route()` → `ask_stream()` |
| GET | `/api/v1/messages` | JWT | `@token_required` → `list_messages_route()` → `list_messages()` |
| GET | `/api/v1/messages/<id>` | JWT | `@token_required` → `get_message_route()` → `get_message()` |
| DELETE | `/api/v1/messages/<id>` | JWT | `@token_required` → `delete_message_route()` → `delete_message()` |
| DELETE | `/api/v1/messages` | JWT | `@token_required` → `delete_all_messages_route()` → `delete_all_messages()` |

#### 5e. `app.register_blueprint(auth_bp)` — `app.py:27`

```
File: backend/routes/auth_routes.py, line 5
```

Registers 4 routes under `/api/v1/auth`:

| Method | Path | Auth | Decorator chain |
|--------|------|:----:|-----------------|
| POST | `/api/v1/auth/register` | No | `register_user()` → `register()` |
| POST | `/api/v1/auth/login` | No | `login_user()` → `login()` |
| POST | `/api/v1/auth/logout` | JWT | `@token_required` → `logout_user()` → `logout()` |
| GET | `/api/v1/auth/me` | JWT | `@token_required` → `get_logged_in_user()` → `get_current_user()` |

---

### 6. `app.run(debug=False, threaded=True)` — `app.py:41`

```
File: backend/app.py, line 41
```

- Starts Werkzeug development server on `http://127.0.0.1:5000`
- `debug=False` — no reloader, no debugger
- `threaded=True` — each request gets its own thread
- The server blocks here until `KeyboardInterrupt` or crash

**Why:** This is the line that begins serving HTTP traffic. All initialization must complete before this point.

---

## Startup Ordering Summary

```
Step  File                                  Duration    What Happens
────  ────────────────────────────────────  ─────────── ─────────────────────────────
0     backend/app.py (import)               ~10ms       All modules imported, classes loaded
1     backend/app.py:32 (load_dotenv)       ~5ms        .env → os.environ
2     backend/app.py:33 (setup_logging)     ~5ms        Console + file log handlers
3a    src/core/engine_factory.py:42         ~500ms      4 JSON files loaded, SearchEngine assembled
3b    src/core/reranker.py:13               ~1ms        Reranker created (no data loaded)
3c    src/workflows/retrieval_workflow.py:5  ~1ms        Composes engine + reranker
3d    src/llm/rag_repository.py:40          ~200ms      Ollama client created, article lookup built
3e    src/llm/rag_formatter.py:1            ~1ms        Stateless formatter
3f    services/qa_service.py:32             ~1ms        RAGWorkflow stored in _workflow global
4     src/core/text_processor.py:8          ~300ms      spaCy pipeline initialized (cached)
5a    backend/app.py:20                     ~5ms        Flask app created
5b    backend/app.py:21                     ~1ms        CORS wrapped
5c    config/db_connect.py:15               ~200ms      MongoDB connection established
5d    backend/app.py:26                     ~1ms        API blueprint registered (8 routes)
5e    backend/app.py:27                     ~1ms        Auth blueprint registered (4 routes)
6     backend/app.py:41                     —           Server starts listening (:5000)
────  ────────────────────────────────────  ─────────── ─────────────────────────────
      Total startup time                    ~1.2-1.5s
```

---

## Dependency Injection Summary

The backend uses **manual constructor injection** (no DI framework). The assembly chain:

```
EngineFactory.from_artifacts()
    └── produces SearchEngine
            └── injected into RetrievalWorkflow(engine, reranker)
                    └── injected into RAGRepository(retrieval_workflow)
                            └── injected into RAGWorkflow(repository, formatter)
                                    └── stored in module global _workflow in qa_service.py
```

Each layer receives its dependencies explicitly via `__init__` parameters. No service locator, no inversion-of-control container.

---

## What is NOT Initialized at Startup

| Component | When Initialized | Where |
|-----------|-----------------|-------|
| Ollama connectivity check | First `/ask?use_llm=true` request | `rag_repository.py:291` (`_ensure_ollama_checked()`) — cached per process lifetime |
| spaCy pipeline (if not yet) | First `process_text()` call | `text_processor.py:36` (`_get_nlp()`) — lazy via module-level `_spacy_nlp` |
| Reranker vector cache | First `rerank()` call | `reranker.py:29` (`_get_tf_vector()`) — populated lazily per doc |
| Ingestion pipeline | Manual CLI invocation | `python -m preprocessing_scripts.run_ingestion` |

## Frontend Startup

The frontend is a separate process (Vite dev server):

```
cd frontend && npm run dev
→ Vite dev server on http://localhost:5173
→ Hot Module Replacement enabled
→ Proxies API requests to backend (configured in vite.config.js)
```

No connection to the backend is made until the user submits a query.
