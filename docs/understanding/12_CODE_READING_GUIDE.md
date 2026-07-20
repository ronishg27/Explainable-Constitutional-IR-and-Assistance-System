# Code Reading Guide

**Goal:** Maximize understanding with minimal jumping. Each file builds on the previous one.

---

## Phase 1 — Surface Layer (4 files)

Understand what the system does and how to run it.

### 1. `docs/understanding/01_SYSTEM_OVERVIEW.md`

| | |
|---|---|
| **Why now** | Shortest path to knowing what this project is, who uses it, and what it does |
| **Prerequisites** | None |
| **Knowledge gained** | Problem domain, users, capability list, technology stack, high-level architecture diagram |

### 2. `docs/understanding/02_REPOSITORY_TOUR.md`

| | |
|---|---|
| **Why now** | Map of the filesystem — know where everything lives before reading any code |
| **Prerequisites** | 01_SYSTEM_OVERVIEW |
| **Knowledge gained** | Every top-level directory's purpose, entry points, where business logic vs infrastructure lives, the 15 most important files |

### 3. `backend/app.py`

| | |
|---|---|
| **Why now** | The entry point. Understanding startup is prerequisite to understanding runtime. Also the shortest real file in the project. |
| **Prerequisites** | Repository tour |
| **Knowledge gained** | How the server starts, initialization order, where blueprints are registered, the `main()` function |

### 4. `frontend/src/App.jsx`

| | |
|---|---|
| **Why now** | The frontend entry point. Short, gives the full route table. |
| **Prerequisites** | None |
| **Knowledge gained** | All frontend routes, auth wrapper, page component mapping |

---

## Phase 2 — Request Flow (4 files)

Understand how a request travels through the system.

### 5. `backend/routes/api_routes.py`

| | |
|---|---|
| **Why now** | The routing table — every HTTP endpoint in one file |
| **Prerequisites** | app.py (knowing blueprints are registered) |
| **Knowledge gained** | All API endpoints, which are protected, which controller handles each |

### 6. `backend/controllers/api_controller.py`

| | |
|---|---|
| **Why now** | The HTTP-to-domain boundary. See exactly how requests are validated, delegated, and responses are assembled. |
| **Prerequisites** | api_routes.py (knows which routes map here) |
| **Knowledge gained** | Validation logic, `QAService` delegation, streaming SSE pattern, persistence call, error handling |

### 7. `backend/controllers/decorators.py`

| | |
|---|---|
| **Why now** | Authentication is applied before every protected route. Understanding the JWT flow is essential to understanding the system. |
| **Prerequisites** | api_controller.py (sees `@token_required` in use) |
| **Knowledge gained** | JWT extraction (header + cookie fallback), decode, token_version invalidation, `request.user` attachment |

### 8. `backend/services/qa_service.py`

| | |
|---|---|
| **Why now** | The bridge between controllers and domain. Knows how the pipeline is initialized and how persistence works. |
| **Prerequisites** | api_controller.py (sees `QAService.answer_query()` called) |
| **Knowledge gained** | `init_workflow()` assembly, module-global `_workflow` singleton, `persist_message()` persistence logic |

---

## Phase 3 — Domain Core (6 files)

Understand the IR engine — the heart of the system.

### 9. `backend/src/core/document.py`

| | |
|---|---|
| **Why now** | The domain dataclass used everywhere in the IR engine. Understand the data shape before algorithms. |
| **Prerequisites** | None |
| **Knowledge gained** | All fields of a Document (doc_id, part_no, article_no, title, text, citation, level, boost, etc.) |

### 10. `backend/src/core/text_processor.py`

| | |
|---|---|
| **Why now** | All text in the system flows through this. Understanding the two-processor design is prerequisite to understanding BM25 and proximity scoring. |
| **Prerequisites** | document.py (knows what text is being processed) |
| **Knowledge gained** | Normalization pipeline (contractions, lowercase, alpha-only), spaCy lemmatization, stopword filtering, the two-processor split (BM25 vs proximity) |

### 11. `backend/src/core/bm25_scorer.py`

| | |
|---|---|
| **Why now** | The primary ranking algorithm. Short, pure math. |
| **Prerequisites** | text_processor.py (knows how BM25 tokens are produced) |
| **Knowledge gained** | BM25 formula with `k1=1.5`, `b=1.0`, IDF computation, edge case handling (df=0, doc_len=0, tf=0), `matched_terms()` |

### 12. `backend/src/core/proximity.py`

| | |
|---|---|
| **Why now** | The second ranking signal. Introduces positional indexing and pair-based scoring. |
| **Prerequisites** | text_processor.py (knows how proximity tokens differ from BM25 tokens) |
| **Knowledge gained** | Positional index lookup, pair generation heuristic (all-pairs ≤5, adjacent >5), two-pointer minimum-distance algorithm, quadratic inverse score formula |

### 13. `backend/src/core/search_engine.py`

| | |
|---|---|
| **Why now** | The main retrieval algorithm. Combines everything from steps 9-12 into the Phase 1 hybrid scoring pipeline. |
| **Prerequisites** | document.py (data shape), text_processor.py (tokenization), bm25_scorer.py (BM25), proximity.py (proximity) |
| **Knowledge gained** | Full Phase 1 pipeline: tokenize → expand → generate candidates → score each (BM25 + title boost + proximity) → sort → return top-k. Title token pre-computation. `_score_document()` internals. |

### 14. `backend/src/core/reranker.py`

| | |
|---|---|
| **Why now** | Phase 2 of retrieval. The most algorithmically dense file. |
| **Prerequisites** | search_engine.py (sources the results being reranked), bm25_scorer.py (tf_index for cosine similarity) |
| **Knowledge gained** | RRF fusion formula, MMR diversity iterative algorithm, sparse TF vector cosine similarity, rule-based boost configuration |

---

## Phase 4 — Workflow Composition (3 files)

Understand how the pieces fit together.

### 15. `backend/src/workflows/retrieval_workflow.py`

| | |
|---|---|
| **Why now** | The first composition layer — wires SearchEngine + Reranker. Short but critical. |
| **Prerequisites** | search_engine.py, reranker.py |
| **Knowledge gained** | Default recall_k=50 and top_k=8, the `retrieve()` pipeline, how Phase 1 and Phase 2 are connected |

### 16. `backend/src/llm/rag_repository.py`

| | |
|---|---|
| **Why now** | The second composition layer — wires RetrievalWorkflow + Ollama. Also owns article promotion and context truncation. |
| **Prerequisites** | retrieval_workflow.py (delegated to by `retrieve()`), document.py (article data shape) |
| **Knowledge gained** | Article promotion algorithm (group → merge → dedup → track clauses), Ollama client creation, lazy connectivity check, 3-attempt retry loop, `build_truncated_text()` for LLM context efficiency |

### 17. `backend/src/llm/rag_workflow.py`

| | |
|---|---|
| **Why now** | The top-level orchestrator. Understand how retrieval + LLM + error handling come together. |
| **Prerequisites** | rag_repository.py (delegates to it), rag_formatter.py (uses it) |
| **Knowledge gained** | `ask()` decision matrix (LLM on/off, connectivity, model availability, retry failure), streaming generator pattern, response assembly |

---

## Phase 5 — Persistence & Auth (3 files)

Understand how data is stored and users are managed.

### 18. `backend/services/article_service.py`

| | |
|---|---|
| **Why now** | The upsert-by-doc_id pattern that keeps `referenced_articles` deduplicated. |
| **Prerequisites** | rag_workflow.py (sees articles being persisted) |
| **Knowledge gained** | Upsert logic, field update strategy, error handling |

### 19. `backend/services/message_service.py`

| | |
|---|---|
| **Why now** | The full CRUD for Q&A history — pagination, ownership, search, delete. |
| **Prerequisites** | article_service.py (similar pattern), controllers/api_controller.py (sees endpoints that call these) |
| **Knowledge gained** | Pagination implementation, user-ownership enforcement |

### 20. `backend/controllers/auth_controller.py`

| | |
|---|---|
| **Why now** | Registration, login, logout — the auth flow end-to-end. |
| **Prerequisites** | decorators.py (knows JWT format), user_model.py (knows User data shape) |
| **Knowledge gained** | Password hashing with bcrypt, JWT creation, token version increment on logout, cookie setting |

---

## Phase 6 — Frontend (4 files)

Understand the UI surface.

### 21. `frontend/src/api/client.js`

| | |
|---|---|
| **Why now** | Every frontend request goes through this. Understand the fetch wrapper, token injection, error handling. |
| **Prerequisites** | app.jsx (knows the frontend structure) |
| **Knowledge gained** | `apiClient()` pattern, `getToken()`/`setToken()`, 100s timeout, 401 redirect |

### 22. `frontend/src/context/AuthProvider.jsx`

| | |
|---|---|
| **Why now** | The auth state management — login, logout, token storage, user state. |
| **Prerequisites** | client.js (used for API calls), controllers/auth_controller.py (knows backend auth endpoints) |
| **Knowledge gained** | localStorage token persistence, login/register/logout flows, context pattern |

### 23. `frontend/src/hooks/useAskStream.js`

| | |
|---|---|
| **Why now** | SSE streaming — the most technically interesting frontend file. |
| **Prerequisites** | client.js (uses apiClient), rag_workflow.py (knows the backend streaming protocol) |
| **Knowledge gained** | `ReadableStream.getReader()` SSE consumption, AbortController cancellation, event types |

### 24. `frontend/src/components/mainsearchbar.jsx`

| | |
|---|---|
| **Why now** | The main feature component. See how query state, streaming, results, error handling, and suggestions all wire together. |
| **Prerequisites** | useAskStream.js (used for streaming), Resultdisplay.jsx (renders results), Toggle/Button/Alert (UI primitives) |
| **Knowledge gained** | Full component lifecycle: input → submit → stream → display → error/cancel |

---

## Phase 7 — Deeper Dives (4 files)

For readers who want to understand the edges.

### 25. `backend/src/core/engine_factory.py`

| | |
|---|---|
| **Why now** | How the entire IR engine is assembled from disk artifacts. The startup dependency graph. |
| **Prerequisites** | All src/core/ files (documents, scorers, search engine) |
| **Knowledge gained** | File loading order, TextProcessor creation with correct flags, synonym expander wiring, SearchEngine construction |

### 26. `backend/src/core/query_expander.py`

| | |
|---|---|
| **Why now** | Synonym expansion logic — how 44 groups improve recall without over-expanding. |
| **Prerequisites** | text_processor.py (tokens being expanded), search_engine.py (where expansion is applied) |
| **Knowledge gained** | Group lookup construction, multi-word phrase guard, deduplication |

### 27. `backend/src/core/index_builder.py`

| | |
|---|---|
| **Why now** | Offline ingestion — how the three indexes are built from the flattened corpus. |
| **Prerequisites** | document.py (data shape), text_processor.py (tokenization) |
| **Knowledge gained** | TF index construction (count), positional index construction (list positions), doc stats computation |

### 28. `backend/src/llm/rag_formatter.py`

| | |
|---|---|
| **Why now** | The LLM prompt templates. Smallest file in the project, but contains the grounding instructions that define answer quality. |
| **Prerequisites** | rag_workflow.py (sees formatter being called) |
| **Knowledge gained** | Context formatting, system prompt (grounding rules, style adaptation by question type), user prompt template |

---

## Suggested Reading Order

```
Phase 1 — Surface
  ┌── 01_SYSTEM_OVERVIEW.md
  ├── 02_REPOSITORY_TOUR.md
  ├── backend/app.py
  └── frontend/src/App.jsx

Phase 2 — Request Flow
  ├── backend/routes/api_routes.py
  ├── backend/controllers/api_controller.py
  ├── backend/controllers/decorators.py
  └── backend/services/qa_service.py

Phase 3 — Domain Core
  ├── backend/src/core/document.py
  ├── backend/src/core/text_processor.py
  ├── backend/src/core/bm25_scorer.py
  ├── backend/src/core/proximity.py
  ├── backend/src/core/search_engine.py
  └── backend/src/core/reranker.py

Phase 4 — Workflow Composition
  ├── backend/src/workflows/retrieval_workflow.py
  ├── backend/src/llm/rag_repository.py
  └── backend/src/llm/rag_workflow.py

Phase 5 — Persistence & Auth
  ├── backend/services/article_service.py
  ├── backend/services/message_service.py
  └── backend/controllers/auth_controller.py

Phase 6 — Frontend
  ├── frontend/src/api/client.js
  ├── frontend/src/context/AuthProvider.jsx
  ├── frontend/src/hooks/useAskStream.js
  └── frontend/src/components/mainsearchbar.jsx

Phase 7 — Deeper Dives
  ├── backend/src/core/engine_factory.py
  ├── backend/src/core/query_expander.py
  ├── backend/src/core/index_builder.py
  └── backend/src/llm/rag_formatter.py
```

Total: 28 files across 7 phases, progressing from 5-minute overviews to 30-minute deep dives.
