# Constitution Assistant — Repository Tour

## Root Directory

**Purpose:** Project container — orchestration, documentation, and metadata lives here.

| File | Purpose |
|---|---|
| `Makefile` | Quick-start commands (`make run`, `make backend`, `make frontend`) |
| `AGENTS.md` | Instructions for AI coding assistants navigating the repo |
| `.prettierrc` | Code formatting config (frontend concern, placed at root) |

The root is **infrastructure** — no business logic. It ties the two apps together.

---

## `backend/` — Flask API + IR Engine

**Purpose:** Everything server-side. The core of the system.

### Subdirectories (in order of a request's journey):

#### `routes/` — API surface
- **Files:** `api_routes.py` (Q&A endpoints), `auth_routes.py` (auth endpoints)
- **Purpose:** Flask Blueprints — thin URL-to-function mapping, no logic
- **Interactions:** Calls controllers
- **Nature:** Infrastructure

#### `controllers/` — Request validation and orchestration
- **Files:** `api_controller.py` (ask/ask-stream/message CRUD), `auth_controller.py` (register/login/logout), `decorators.py` (JWT `@token_required`)
- **Purpose:** Validate input → delegate to services → format responses. `_persist_message()` lives here.
- **Interactions:** Calls services
- **Nature:** Thin orchestration layer (some business logic in validation rules)

#### `services/` — Business logic facades
- **Files:** `qa_service.py` (lazy singleton RAGWorkflow, `answer_query()`), `user_service.py`, `message_service.py`, `article_service.py`
- **Purpose:** Higher-level orchestration that doesn't belong in pure engine code but isn't HTTP-aware either
- **Interactions:** `qa_service.py` calls into `src/llm/` and `src/core/`; the others talk to models (MongoDB)
- **Nature:** Business logic

#### `src/core/` — The IR Engine (no Flask dependency)
- **Files:** `search_engine.py`, `bm25_scorer.py`, `proximity.py`, `reranker.py`, `text_processor.py`, `engine_factory.py`, `query_expander.py`, `index_builder.py`, `document.py`
- **Purpose:** Pure Python BM25 + proximity + reranking. This is the project's crown jewel.
- **Interactions:** Called by `src/workflows/` and `src/llm/`. Zero Flask/HTTP coupling.
- **Nature:** Core business logic

#### `src/llm/` — RAG Layer
- **Files:** `rag_repository.py` (retrieval + Ollama client + article promotion), `rag_formatter.py` (prompt construction), `rag_workflow.py` (orchestrator)
- **Purpose:** Bridges retrieval engine and LLM; handles context truncation, prompt building, retry logic
- **Interactions:** Uses `src/workflows/` for retrieval, calls Ollama externally
- **Nature:** Business logic

#### `src/workflows/` — Orchestration Workflows
- **Files:** `retrieval_workflow.py` (search → rerank pipeline), `ingestion_workflow.py` (offline index building)
- **Purpose:** Higher-level compositions of core engine components
- **Interactions:** Calls `src/core/` components
- **Nature:** Business logic

#### `src/constants/` — Static data
- **Files:** `contraction_map.py` (57 contractions), `stopwords.py` (~120 stopwords)
- **Nature:** Infrastructure/data

#### `models/` — MongoDB ODM (mongoengine)
- **Files:** `user_model.py`, `message_model.py`, `referenced_article_model.py`
- **Interactions:** Used by services for persistence
- **Nature:** Infrastructure (data mapping)

#### `config/` — Connection management
- **Files:** `db_connect.py` (MongoDB singleton), `log_config.py`
- **Nature:** Infrastructure

#### `preprocessing_scripts/` — One-time offline pipeline
- **Files:** `run_ingestion.py` (full pipeline), `flatten_constitution.py` (nested JSON → flat docs), `build_index.py` (flat docs → indexes)
- **Interactions:** Writes to `data/output/`. Called manually, not at runtime.
- **Nature:** Infrastructure/tooling

#### `data/` — Input data and generated artifacts
- **Files:** `nepal_constitution_new.json` (nested input), `synonyms.json` (44 groups), `output/tf_index.json`, `output/pos_index.json`, `output/doc_stats.json` (generated)
- **Nature:** Data

#### `temp/tests/` — Test suite
- **Nature:** Verification

---

## `frontend/` — React 19 SPA

**Purpose:** Browser UI.

### Subdirectories:

| Folder | Purpose |
|---|---|
| `src/pages/` | Page-level components (Home, Login, Register, History, MessageDetail, About, HowItWorks, NotFound) |
| `src/components/` | Reusable UI (Navbar, MainSearchBar, ResultDisplay, ArticleCard, Suggestion, ConfidenceBadge, ProtectedRoute) + `ui/` primitives (Button, Input, Toggle, Card, Alert, Badge, Spinner, Pagination, Dialog) |
| `src/context/` | Auth context (`AuthProvider.jsx`, `useAuth.js`) — JWT stored in localStorage |
| `src/hooks/` | `useAskStream.js` — SSE streaming hook |
| `src/api/` | `client.js` — fetch wrapper with Bearer token and timeout |
| `src/utils/` | `highlight.jsx` — term highlighting in article cards |
| `main.jsx` | Mount point |
| `App.jsx` | Router + AuthProvider wrapper |

**Interactions with backend:** REST calls to Flask API with JWT Bearer auth. SSE for streaming. **Nature:** UI with no business logic — all intelligence is server-side.

---

## `docs/` — Documentation

**Files:** `PROJECT_DOCUMENTATION.md` (the source of truth), `api_docs.md`, `algorithm_details.md`, `design.md`, `SYSTEM_OVERVIEW.md`, `mermaid/` (diagrams)

---

## Other Top-Level Directories

| Directory | Purpose |
|---|---|
| `postman/` | API testing collection |
| `references/` | Academic PDF papers |
| `temp/` | Scratch notes, temporary files |

---

## Where everything lives

| Question | Answer |
|---|---|
| **Where does the application start?** | `backend/app.py` — Flask factory, `app.run()`. |
| **Where do requests begin?** | `backend/routes/api_routes.py` — Blueprint maps URLs to controllers. |
| **Where does business logic live?** | `backend/src/core/` (IR engine), `backend/src/llm/` (RAG), `backend/src/workflows/` (orchestration), `backend/services/qa_service.py`. |
| **Where does persistence happen?** | `backend/services/message_service.py` and `article_service.py` → mongoengine models → MongoDB. |
| **Where does configuration live?** | `backend/.env` (secrets/URLs), `backend/config/db_connect.py` (MongoDB), `backend/.env.sample` (shape reference). |
| **Where do tests live?** | `backend/temp/tests/` (pytest). |

---

## If I only read 15 files to understand the project, these are the files

| # | File | Why |
|---|---|---|
| 1 | `docs/PROJECT_DOCUMENTATION.md` | Everything in one place |
| 2 | `backend/app.py` | Entry point, factory, wiring |
| 3 | `backend/routes/api_routes.py` | API surface — what endpoints exist |
| 4 | `backend/controllers/api_controller.py` | Request handling — ask, ask-stream, persist |
| 5 | `backend/controllers/decorators.py` | JWT auth enforcement |
| 6 | `backend/services/qa_service.py` | Q&A orchestration and decision matrix |
| 7 | `backend/src/core/search_engine.py` | Hybrid search (BM25 + proximity + title boost) |
| 8 | `backend/src/core/bm25_scorer.py` | BM25 scoring |
| 9 | `backend/src/core/proximity.py` | Term proximity scoring |
| 10 | `backend/src/core/reranker.py` | RRF + MMR + rule boost |
| 11 | `backend/src/core/text_processor.py` | Tokenization pipeline |
| 12 | `backend/src/llm/rag_repository.py` | Retrieval + article promotion + Ollama client |
| 13 | `backend/models/user_model.py` | User schema + auth methods |
| 14 | `backend/models/message_model.py` | Message schema with article references |
| 15 | `frontend/src/pages/HomePage.jsx` | Main user-facing interface — search, toggle, streaming display |
| (bonus) | `backend/src/workflows/retrieval_workflow.py` | Connects search → rerank into one pipeline |
| (bonus) | `frontend/src/hooks/useAskStream.js` | SSE streaming — the most interesting frontend code |
