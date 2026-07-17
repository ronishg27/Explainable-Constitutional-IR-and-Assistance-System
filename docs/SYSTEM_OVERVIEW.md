# Constitution Assistant — System Overview

## 1. What problem does this project solve?

Citizens, lawyers, and students need to ask natural-language questions about the **Constitution of Nepal (2072 / 2015)** and get **grounded, citable answers** — not LLM hallucinations. The project replaces manual legal research with a specialized search + RAG system that returns both the relevant constitutional provisions and an AI-generated answer strictly limited to those provisions.

## 2. Who are the users?

- **General public** — Nepali citizens asking about their constitutional rights
- **Legal professionals** — lawyers and judges researching provisions
- **Students & academics** — studying constitutional law
- **Administrators** — managing the system

## 3. What are the major capabilities?

| Capability | Description |
|---|---|
| **Hybrid Legal Search** | Custom BM25 + term proximity + title boost retrieval engine tuned for legal text |
| **RAG (Retrieval-Augmented Generation)** | Local LLM (Ollama) answers grounded strictly in retrieved articles |
| **Synonym Expansion** | 44 legal synonym groups (e.g., arrest/detention/custody) to improve recall |
| **Multi-stage Reranking** | RRF fusion + MMR diversity + rule-based boost for precision and diversity |
| **Article Promotion** | Clause/sub-clause results merged into full articles with matched-clause tracking |
| **Streaming Responses** | SSE-based real-time token delivery for LLM answers |
| **User Authentication** | JWT-based registration, login, logout with token version invalidation |
| **Chat History** | Full CRUD with pagination, ownership enforcement |
| **Graceful Degradation** | Falls back to retrieval-only if Ollama is unavailable |
| **Offline Ingestion Pipeline** | Preprocesses nested JSON constitution into search indexes |

## 4. What are the major components/modules?

```
Constitution Assistant
├── Backend (Flask / Python 3.13)
│   ├── Routes (Blueprints)      ── HTTP endpoints
│   ├── Controllers              ── Input validation, orchestration
│   ├── Services                 ── QA orchestration, user/message/article CRUD
│   ├── IR Engine (src/core/)    ── BM25, proximity, search, reranker
│   ├── RAG Layer (src/llm/)     ── Retrieval, prompt formatting, Ollama client
│   ├── Models (ODM)             ── User, Message, ReferencedArticle
│   ├── Preprocessing Scripts    ── Flatten JSON → build indexes
│   └── Config                   ── MongoDB connection singleton
├── Frontend (React 19 / Vite 8)
│   ├── Pages                    ── Home, Login, Register, History, etc.
│   ├── Components               ── SearchBar, ResultDisplay, ArticleCard, etc.
│   ├── UI Primitives            ── Button, Input, Card, Spinner, etc.
│   ├── Auth Context             ── JWT management, login/logout
│   └── Streaming Hook           ── SSE reader for real-time answers
└── Infrastructure
    ├── MongoDB 8                ── Users, messages, referenced articles
    └── Ollama (optional)        ── Local LLM inference (default: qwen3:8b)
```

## 5. How does data flow through the system?

**Offline path:**
```
nepal_constitution.json (nested)
  → flatten_constitution.py → ~700 flat documents
  → IndexBuilder → tf_index.json + pos_index.json + doc_stats.json
```

**Online Q&A path:**
```
User query (plain English)
  → SearchEngine: tokenize → synonym expansion → BM25 + proximity + title boost
  → Reranker: RRF fusion → MMR diversity → rule boost
  → Article Promotion: clauses → merged articles (top 8)
  → [Optional] Ollama LLM: truncated context → grounded answer
  → MongoDB persistence: upsert articles, save message
  → Response: provisions + citations + [optional] LLM answer
```

## 6. Which technologies and frameworks are used?

| Layer | Technology |
|---|---|
| Backend | Python 3.13, Flask 3.x, mongoengine ODM, spaCy, PyJWT, bcrypt |
| Frontend | React 19, Vite 8, Tailwind CSS v4, react-router-dom, react-markdown |
| Database | MongoDB 8 |
| IR Engine | **Custom Python** — no Elasticsearch/Solr |
| LLM | Ollama (local), default model `qwen3:8b` |
| Auth | JWT (HS256, 12h expiry) + token versioning |

## 7. What architectural style is used?

**Layered monolith with a service-oriented internal design.** The backend is a single Flask process with clear separation:
- **Routes layer** (thin blueprints) → **Controllers** (validation) → **Services** (orchestration) → **Core engine** (pure logic, no Flask deps)
- The IR engine (`src/core/`) is framework-agnostic and independently testable
- Frontend is a separate SPA communicating via REST + SSE

## 8. Which parts seem most important?

1. **`src/core/search_engine.py`** — the custom hybrid search engine (BM25 + proximity + title boost); it's the heart of retrieval quality
2. **`src/core/reranker.py`** — RRF + MMR + rule boost determines final ranking
3. **`src/llm/rag_repository.py`** — bridges retrieval and LLM; handles article promotion, context truncation, and Ollama integration
4. **`controllers/api_controller.py`** — the main `ask()` and `ask_stream()` endpoints plus message persistence
5. **The three index files** (`tf_index.json`, `pos_index.json`, `doc_stats.json`) — generated offline, loaded at startup, essential for all retrieval

## 9. Which parts are supporting infrastructure?

- **User authentication** (routes/controllers/models) — required but not core to the constitutional Q&A mission
- **Chat history CRUD** — convenience feature
- **Frontend UI components** — replaceable; the API is the real product
- **Preprocessing scripts** — run once, produce artifacts; not in the critical runtime path
- **`json_builder_tools/`** — browser JSON editing helpers, mostly tooling
- **Tests** (`backend/temp/tests/`) — verification, not production

## 10. Architecture diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React 19 + Vite 8)                  │
│                                                                  │
│  AuthProvider (JWT → Bearer header)                              │
│  useAskStream (SSE reader for streaming tokens)                  │
│                                                                  │
│  Pages: Home│Login│Register│History│MessageDetail│About│HowItWorks│
│  Components: Navbar│MainSearchBar│ResultDisplay│ArticleCard      │
│  UI: Button│Input│Toggle│Card│Alert│Badge│Spinner│Dialog         │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP/SSE (JWT auth)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                  BACKEND (Flask / Python 3.13)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  ROUTES (api_routes.py, auth_routes.py)                  │    │
│  │  /ask │ /ask-stream │ /messages │ /auth/*               │    │
│  └────────────────────┬─────────────────────────────────────┘    │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  CONTROLLERS (api_controller.py, auth_controller.py)     │    │
│  │  Validation ← JWT decorator → _persist_message()         │    │
│  └────────────────────┬─────────────────────────────────────┘    │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  SERVICES (qa_service.py, user_service.py, etc.)         │    │
│  │  QAService.answer_query() → RAGWorkflow.ask()           │    │
│  └────────────────────┬─────────────────────────────────────┘    │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  RAG LAYER (src/llm/)                                    │    │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐     │    │
│  │  │RAGRepository│ │RAGFormatter  │ │ollama_llm.py   │     │    │
│  │  │(retrieve +  │ │(prompts)     │ │(Ollama client  │     │    │
│  │  │ promote +   │ │              │ │ factory)       │     │    │
│  │  │ call_llm)   │ │              │ │                │     │    │
│  │  └──────┬──────┘ └──────────────┘ └────────────────┘     │    │
│  └─────────┼─────────────────────────────────────────────────┘    │
│            ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  IR ENGINE (src/core/) — PURE PYTHON, NO FLASK DEPS     │    │
│  │                                                         │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │    │
│  │  │BM25Scorer│  │Proximity │  │SearchEng │  │Reranker │ │    │
│  │  │(k1=1.5   │  │Scorer    │  │ine       │  │RRF+MMR  │ │    │
│  │  │b=1.0)    │  │(pairs)   │  │(hybrid)  │  │+boost)  │ │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │    │
│  │                    ┌──────────────┐                     │    │
│  │                    │QueryExpander│ (44 syn groups)      │    │
│  │                    └──────────────┘                     │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  MISC:  Models (User/Message/Article)  │  Config (MongoDB)       │
└──────────────────────────┬───────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        MongoDB 8      Ollama (opt)   Data/Indexes
        ECIRAS DB      qwen3:8b       tf_index.json
        users │ msgs │ articles       pos_index.json
                                       doc_stats.json
```

## 11. 5-minute pitch to a senior engineer

**Constitution Assistant** is a RAG system for the Constitution of Nepal, built as a layered Flask monolith serving a React SPA.

The interesting part is the **custom IR engine** in `src/core/` — it doesn't use Elasticsearch or any off-the-shelf search library. Instead, it implements BM25 (`k1=1.5`, `b=1.0`) with a proximity scoring heuristic (ordered term pairs, capped at 30-token windows) and title boosting (5x per title match). The top 30 candidates go through a 3-stage reranker: RRF fusion (k=60) of the BM25/proximity/title signals, then MMR diversity (λ=0.5) via BM25 cosine similarity, then a rule-based boost factoring in document-level, part-level, and hierarchical-level multipliers. Clause/sub-clause results are promoted to article level post-reranking with matched-clause tracking.

**Key design choices:** `b=1.0` (full length normalization) for varied-length legal provisions; two separate text processors (lemmatized+stopwords-removed for BM25, raw+stopwords-preserved for proximity); synonym expansion from 44 legal synonym groups applied only to BM25 tokens; and Ollama is optional — the system degrades gracefully to retrieval-only.

The backend delivers via two endpoints: `/ask` (JSON) and `/ask-stream` (SSE), both JWT-protected, both persisting results to MongoDB through a fire-and-forget `_persist_message()` hook that never breaks the response.

The frontend is standard React 19 with Tailwind v4 — auth context for JWT, SSE hook for streaming, reusable UI primitives. Nothing exotic there.

**Biggest piece of technical debt:** the async `def` methods in `message_service.py` and `article_service.py` look like they should be awaitable but aren't — they use synchronous mongoengine calls, so they're misleading but functionally correct. The service layer has more development potential, e.g., admin APIs exist in `UserService` but no admin blueprint wires them up.
