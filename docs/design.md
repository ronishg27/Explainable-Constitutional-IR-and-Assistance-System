# Constitution Assistant — Design Document

## 1. Overview

**Constitution Assistant** is a Retrieval-Augmented Generation (RAG) system that answers natural-language questions about the Constitution of Nepal (2072 / 2015). Users ask legal questions in plain English, and the system returns relevant constitutional articles ranked by a custom hybrid search engine, optionally enhanced with an LLM-generated answer grounded strictly in the retrieved provisions.

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React 19 + Vite 8)             │
│  Navbar │ SearchBar │ MainSearchBar │ ResultDisplay │ Suggs.│
└───────────────────────────┬─────────────────────────────────┘
                            │ POST /api/v1/ask (JWT auth)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (Flask / Python 3.13)              │
│                                                              │
│  ┌──────────┐  ┌────────────┐  ┌─────────────────────────┐ │
│  │  Routes   │  │Controllers │  │      Services            │ │
│  │(Blueprints)│  │(validation)│  │  QAService (singleton)   │ │
│  └──────────┘  └────────────┘  └──────────┬──────────────┘ │
│                                            │                │
│                    ┌───────────────────────┼───────────┐    │
│                    │     RAGWorkflow       │           │    │
│                    │  ┌─────────────────┐  │           │    │
│                    │  │  RAGRepository   │  │           │    │
│                    │  │  (retrieval +    │  │           │    │
│                    │  │   Ollama client)  │  │           │    │
│                    │  └────────┬────────┘  │           │    │
│                    │           │           │           │    │
│                    │  ┌────────▼────────┐  │           │    │
│                    │  │RetrievalWorkflow │  │           │    │
│                    │  └─────┬──────┬────┘  │           │    │
│                    │        │      │       │           │    │
│                    │  ┌─────▼──┐ ┌──▼──────┐          │    │
│                    │  │Search  │ │Reranker │          │    │
│                    │  │Engine  │ │(RRF+MMR │          │    │
│                    │  │BM25+prx│ │ +boost) │          │    │
│                    │  └────────┘ └─────────┘          │    │
│                    └──────────────────────────────────┘    │
│                                                              │
│  ┌──────────┐  ┌────────────┐  ┌─────────────────────────┐ │
│  │  Config   │  │   Models   │  │      Preprocessing       │ │
│  │ (MongoDB) │  │(User/Message│  │  (flatten + index build) │ │
│  └──────────┘  │ /Article)   │  └─────────────────────────┘ │
│                └────────────┘                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │      MongoDB 8            │
              │  users / messages /        │
              │  referenced_articles       │
              └───────────────────────────┘
```

## 3. Tech Stack

| Layer          | Technology                          | Details                          |
|----------------|-------------------------------------|----------------------------------|
| Backend        | Python 3.13 + Flask                 | Flask with CORS, Blueprints      |
| Frontend       | React 19 + Vite 8                   | Tailwind CSS v4, JSX             |
| Database       | MongoDB 8 (mongoengine ODM)         | Users, messages, article refs    |
| IR Engine      | Custom Python                       | BM25 + term proximity + title boost |
| NLP            | spaCy (en_core_web_sm)              | Lemmatization, tokenization      |
| LLM            | Ollama (local)                      | Default: gemma3:1b                |
| Auth           | JWT (HS256, 12h expiry)             | httpOnly secure SameSite=Strict cookies + Bearer fallback |
| Tooling        | Prettier, ESLint, Vite HMR          |                                  |

## 4. Layer Details

### 4.1 Backend Layered Architecture

```
app.py → routes/ (Blueprints) → controllers/ (validation) → services/ (orchestration)
                                                                ↓
                                                          src/core/ (retrieval)
                                                          src/llm/ (RAG)
                                                                ↓
                                                          config/ (MongoDB)
                                                          models/ (ODM)
```

- **Routes** (`routes/api_routes.py`, `routes/auth_routes.py`): Flask Blueprints that define URL mappings.
- **Controllers** (`controllers/api_controller.py`, `controllers/auth_controller.py`): Input validation, request parsing, response formatting.
- **Services** (`services/qa_service.py`, `services/user_service.py`, etc.): Business logic orchestration. `QAService` implements a lazy singleton pattern (double-checked locking) for `RAGWorkflow` initialization.
- **Core** (`src/core/`): Pure retrieval logic with no Flask dependency. Testable in isolation.
- **LLM** (`src/llm/`): RAG orchestration, prompt building, Ollama client.

### 4.2 Frontend Component Tree

```
App
├── Navbar          — Top navigation with branding (Constitutional Insight)
├── SearchBar       — Hero header: "Know Your Rights Instantly"
├── MainSearchBar   — Search input + LLM toggle + query submission
│   ├── input field with Enter-key support
│   ├── "Use LLM: ON/OFF" toggle button
│   ├── "Analyze Query" submit button (disabled while loading)
│   └── Suggestion — Quick-suggestion buttons (4 preset queries)
└── ResultDisplay   — Expandable article cards with related-article linking
    └── Article card per result:
        - Collapsed: rank, article number, title, citation
        - Expanded: full provision text, clause details, score, doc ID
        - Related Article section (parent article if result is a clause)
```

## 5. Retrieval Pipeline

### 5.1 Two-Phase Retrieval Pipeline

The `SearchEngine` (`src/core/search_engine.py`) implements candidate-generation + scoring, followed by `Reranker` (RRF fusion + MMR diversity + rule-based boost). The full chain:

```
Query → [BM25 Processor]  ──→ bm25_tokens (lemmatized, no stopwords)
     → [Proximity Processor] ──→ raw_tokens (exact, stopwords kept)
                                      │
                                      ▼
                           Candidate Generation (recall_k=30)
                           (union of doc IDs containing any bm25 token)
                                      │
                                      ▼
                           For each candidate document:
                             score = BM25(k1=1.5, b=0.75)
                                   + title_boost (×5.0 per title token match)
                                   + proximity_weight (×1.0 × avg pair score)
                                      │
                                      ▼
                           Top-30 candidates
                                      │
                                      ▼
                           Reranker.rerank():
                             1. RRF Fusion (combine BM25 + proximity + title ranks)
                             2. MMR Diversity (cosine similarity via BM25 vectors)
                             3. Rule-based Boost (part/level multipliers)
                                      │
                                      ▼
                           Top-8 articles (promoted to article level)
```

### 5.2 BM25 Scoring

Implementation: `src/core/bm25_scorer.py`

Standard BM25 formula with k1=1.5, b=0.75:

```
score(D, Q) = Σ IDF(t) × [tf(t,D) × (k1+1)] / [tf(t,D) + k1 × (1-b + b × |D|/avgdl)]

IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
```

### 5.3 Proximity Scoring

Implementation: `src/core/proximity.py`

- **Pair generation heuristic**: ≤5 query tokens → all unordered pairs; >5 tokens → adjacent pairs only.
- **Distance metric**: Minimum ordered distance between term occurrences.
- **Score function**: `avg(1/(distance+1)²)` — quadratic inverse so close pairs contribute much more.
- **Window cap**: Pairs farther than 30 tokens are discarded (configurable via `max_window`).

### 5.4 Two Text Processors

The engine maintains separate `TextProcessor` instances (`src/core/text_processor.py`):

| Processor | Lemmatization | Stopwords | Used For |
|-----------|:---:|:---:|----------|
| bm25_processor | ON | REMOVED | Candidate generation & BM25 scoring |
| proximity_processor | OFF | KEPT | Proximity pair matching |

Pipeline steps: Normalize (lowercase → expand contractions → alpha-only) → Optional lemmatization (spaCy) → Optional stopword removal.

## 6. RAG Pipeline

Implementation: `src/llm/rag_workflow.py` + `src/llm/rag_repository.py`

### 6.0 Retrieval Layer (`src/llm/rag_repository.py`)

- Owns the `RetrievalWorkflow` (SearchEngine + Reranker) and Ollama client.
- `retrieve()` delegates to `RetrievalWorkflow.retrieve()` for high-recall search + reranking.
- `promote_to_articles()` merges clause/sub-clause results into full articles, deduplicating by `article_no`.
- `call_llm()` calls Ollama with 3-attempt retry logic.
- Connectivity checks are cached per process lifetime.

### 6.1 Prompt Construction (`src/llm/rag_formatter.py`)

- Strict grounding instructions: "answer ONLY from provided articles"
- Citation format: `[Part X, Article Y(Z)]`
- If question is not addressed → explicitly state so

### 6.2 LLM Integration

- Client: `RAGRepository` owns the Ollama client (uses `ollama` Python SDK directly)
- Default model: `gemma3:1b` (configurable via `OLLAMA_MODEL` env)
- Connectivity check: cached, performed once on first request via `RAGRepository.check_ollama_connection()`
- Model check: `RAGRepository.check_model_availability()` verifies configured model exists
- Retry logic: 3 attempts with 0.5s delay via `RAGRepository.call_llm()`
- Graceful fallback: if Ollama is unavailable, API returns HTTP 503; if model missing, returns retrieval-only results with status info

### 6.3 Q&A Endpoint Behavior

| `use_llm` | Ollama Available | HTTP Status | Behavior |
|:---------:|:----------------:|:-----------:|----------|
| false | — | 200 | Return only ranked articles |
| true | yes | 200 | Return LLM answer + article citations |
| true | unreachable | 503 | Error: Ollama service unavailable |
| true | model missing | 200 | Return articles + ollama_status (no LLM answer) |

## 7. Offline Ingestion Pipeline

### 7.1 Pipeline Steps

```
Source JSON (nested constitution)
        │
        ▼
flatten_constitution.py  ──→ flattened_nepal_constitution.json (~700+ flat docs)
        │
        ▼
IngestionWorkflow
  ├── load_documents()        → Document objects
  ├── build_tf_index()        → tf_index.json   (term → {doc_id: tf})
  ├── build_positional_index()→ pos_index.json   (term → {doc_id: [positions]})
  └── compute_doc_stats()     → doc_stats.json   (doc_lengths + avgdl)
        │
        ▼
generate_safe_lemma_dict.py ──→ lemma_dict_v3.json (rule-based corpus lemmas)
```

### 7.2 Running the Pipeline

- `python app.py --rebuild-data` — full rebuild on server start
- `python -m preprocessing_scripts.run_ingestion` — manual pipeline
- `python -m preprocessing_scripts.build_index` — indexes only from existing flattened JSON

### 7.3 Document Schema

```python
@dataclass
class Document:
    doc_id: str
    part_no: str
    article_no: str
    title: str
    text: str
    citation: str
    level: str           # "Part", "Article", "Clause", "SubClause"
    clause_no: str | None
    subclause_id: str | None
```

## 8. Data Models (MongoDB via mongoengine)

### User

| Field         | Type     | Notes                 |
|---------------|----------|-----------------------|
| fullname      | String   | min_length=3, max=50  |
| email         | String   | unique                |
| password_hash | String   | bcrypt hashed         |
| role          | Enum     | user / admin          |
| created_at    | DateTime | auto-set              |
| updated_at    | DateTime | auto-updated on save  |

### Message

| Field      | Type       | Notes                    |
|------------|------------|--------------------------|
| query      | String     | user question            |
| answer     | String     | optional LLM response    |
| user       | Reference  | CASCADE on delete        |
| articles   | List[Ref]  | NULLIFY on delete        |
| created_at | DateTime   |                          |
| updated_at | DateTime   |                          |

### ReferencedArticle

| Field          | Type   | Notes       |
|----------------|--------|-------------|
| title          | String |             |
| citation       | String |             |
| doc_id         | String |             |
| relevance_score| Float  | min_value=0 |
| created_at     | DateTime |           |
| updated_at     | DateTime |           |

## 9. Authentication

- **Method**: JWT (HS256) with 12-hour expiry
- **Storage**: httpOnly secure SameSite=Strict cookies (primary) + Bearer header (fallback)
- **Password hashing**: bcrypt via `bcrypt` library
- **Endpoints**:
  - `POST /api/v1/auth/register` — user registration
  - `POST /api/v1/auth/login` — login, sets JWT cookie
  - `POST /api/v1/auth/logout` — clears JWT cookie (requires auth)
  - `GET /api/v1/auth/me` — current user info (requires auth)

## 10. API Endpoints

| Method | Path                 | Auth | Description                     |
|--------|----------------------|:----:|---------------------------------|
| GET    | `/api/v1`            | No   | API landing + endpoint list     |
| GET    | `/api/v1/health`     | No   | Liveness check                  |
| POST   | `/api/v1/ask`        | Yes  | Main Q&A (`query`, `use_llm`, persists to MongoDB) |
| POST   | `/api/v1/ask-stream` | Yes  | Streaming Q&A via SSE           |
| GET    | `/api/v1/messages`   | Yes  | Paginated chat history          |
| GET    | `/api/v1/messages/<id>` | Yes | Single message with articles  |
| DELETE | `/api/v1/messages/<id>` | Yes | Delete message (owner only)  |
| DELETE | `/api/v1/messages`   | Yes  | Delete all messages            |
| POST   | `/api/v1/auth/register` | No | User registration               |
| POST   | `/api/v1/auth/login` | No   | Login, sets JWT cookie          |
| POST   | `/api/v1/auth/logout`| Yes  | Clears JWT cookie               |
| GET    | `/api/v1/auth/me`    | Yes  | Current user info               |

### 10.1 POST /api/v1/ask — Request

```json
{
  "query": "What is the right to education?",
  "use_llm": true
}
```

**Validation**: JSON required, `query` is string (max 500 chars), `use_llm` defaults to false.

### 10.2 POST /api/v1/ask — Response (retrieval-only)

```json
{
  "query": "What is the right to education?",
  "articles": [
    {
      "doc_id": "31",
      "title": "Right relating to education",
      "citation": "Part 3, Article 31",
      "score": 9.12
    }
  ]
}
```

### 10.3 POST /api/v1/ask — Response (with LLM)

```json
{
  "query": "What is the right to education?",
  "response": "Under the Constitution of Nepal, every citizen has the right to basic education...",
  "articles": [
    {
      "doc_id": "31",
      "title": "Right relating to education",
      "citation": "Part 3, Article 31",
      "score": 9.12
    }
  ],
  "ollama_status": {
    "connected": true,
    "model": "gemma3:1b",
    "model_available": true
  }
}
```

## 11. Configuration

Environment variables (loaded from `backend/.env`):

| Variable         | Default                    | Purpose                   |
|------------------|----------------------------|---------------------------|
| OLLAMA_HOST      | `http://127.0.0.1:11434`   | Ollama server address     |
| OLLAMA_API_KEY   | (empty)                    | Bearer token for Ollama   |
| OLLAMA_MODEL     | `gemma3:1b`                | LLM model name            |
| MONGO_URI        | `mongodb://localhost:27017` | MongoDB connection string |
| MONGO_DB_NAME    | `ECIRAS`                   | Database name             |
| JWT_SECRET       | (required)                 | HS256 signing key         |

## 12. Design Decisions

### 12.1 Hybrid Scoring (BM25 + Proximity + Title Boost)

Combining bag-of-words relevance (BM25) with phrase-level closeness (proximity) and structural metadata (title boost) compensates for each method's weaknesses:
- BM25 captures broad topical relevance but ignores term order.
- Proximity scores capture phrase structure but misses documents without close term pairs.
- Title boost rewards documents whose titles directly match query terms.

### 12.2 Dual Text Processors

Separate processors for BM25 (lemmatized, no stopwords) and proximity (raw, stopwords kept) because:
- Lemmatization improves BM25 recall (matches across morphological forms).
- Stopwords hurt BM25 precision (too common) but are essential for proximity (they carry positional information).

### 12.3 Proximity Pair Heuristic

For queries with >5 tokens, only adjacent pairs are scored rather than all unordered pairs. This avoids O(n²) explosion and empirically captures the most meaningful proximity signals in longer queries.

### 12.4 Lazy Singleton Initialization

`QAService._get_workflow()` uses double-checked locking to build the `SearchEngine` (and its 3 loaded index files) only on the first API request. This keeps server startup fast and avoids loading large indexes when not needed.

### 12.5 Strict RAG Grounding

The prompt explicitly instructs the LLM to answer only from provided articles, cite precisely, and decline to answer if the constitution does not address the question. This prevents hallucination in legal contexts.

### 12.6 Graceful LLM Degradation

If Ollama is unreachable or the configured model is missing, the API falls back to retrieval-only mode with informative status messages rather than failing entirely.

## 13. File/Index Artifacts

All generated in `backend/data/output/`:

| File | Size (approx) | Purpose |
|------|:-----:|---------|
| `flattened_nepal_constitution.json` | ~700+ docs | All articles, clauses, sub-clauses as flat documents |
| `tf_index.json` | — | Term → {doc_id: term frequency} for BM25 |
| `pos_index.json` | — | Term → {doc_id: [positions]} for proximity scoring |
| `doc_stats.json` | — | Document lengths + average document length |
| `lemma_dict_v3.json` | — | Custom lemma map for corpus-specific vocabulary |
