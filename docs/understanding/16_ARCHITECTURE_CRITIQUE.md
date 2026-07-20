# Architecture Critique — Pre-Release Review

---

## Strengths

### 1. Clean layered architecture with clear boundaries
The backend follows a strict layers pattern: **Routes → Controllers → Services → Domain (IR Engine + RAG Layer) → Data**. Each layer has a distinct responsibility and communicates through well-defined interfaces.

- The IR engine (`src/core/`) has zero Flask dependencies — it's pure Python that could be imported into any application.
- The RAG layer (`src/llm/`) depends on the IR engine but not on Flask or the service layer.
- Controllers handle HTTP concerns only (validation, response formatting, JWT extraction).
- This layering makes the engine independently testable, deployable, and replaceable.

### 2. Exceptional error handling and graceful degradation
The system handles failure at every level without crashing:
- MongoDB unreachable at startup → fail-fast (correct for a data-dependent system)
- MongoDB unreachable at runtime → JWT still validates (offline auth mode)
- Ollama unreachable → LLM features disabled, retrieval still works
- LLM call fails after 3 retries → error reported in response body
- spaCy model missing → tokenization works, lemmas are identity
- Persistence failure → logged, doesn't break the response

This is production-quality defensive programming.

### 3. No ML dependencies in the core retrieval engine
The entire IR system uses pure Python: `math.log` for BM25, `math.sqrt` for cosine similarity, and string operations for proximity scoring. This means:
- No numpy, no sklearn, no embedding models, no GPU requirements
- Launch latency is ~1 second (JSON loads + spaCy init)
- Behavior is fully deterministic and auditable
- No "model drift" — the same query always returns the same results

### 4. Well-considered default constants
Every tunable parameter has a documented rationale:
- `b=1.0` (full length normalization) — justified by the variance in legal document length
- `rrf_k=60` — appropriate for 3 signals (BM25 + proximity + title)
- `mmr_lambda=0.5` — equal balance of relevance and diversity
- `recall_k=50` / `top_k=8` — appropriate for a ~700-doc corpus
- `max_window=30` — based on legal clause structure

### 5. Good separation of offline and online concerns
- Ingestion pipeline runs independently of the server
- Indexes are built once, loaded at startup
- No runtime writes to search indexes
- This keeps the online path fast and simple

### 6. Clean frontend architecture
React SPA with standard patterns:
- `AuthProvider` context for JWT management
- `useAskStream` hook for SSE consumption (reusable across components)
- UI primitives as composable presentational components
- Pages as containers that wire primitives + data fetching

---

## Weaknesses

### 1. Async def with synchronous I/O (Medium)
`message_service.py` and `article_service.py` declare methods as `async def` but use synchronous mongoengine calls internally. This is misleading:
- Callers may think they can `await` the methods
- No asyncio event loop is involved — the `async def` decorator creates a coroutine that runs synchronously
- If Flask ever switches to async mode, these methods would need real async implementations

**Suggested fix:** Either remove `async def` and make them synchronous, or implement real async MongoDB access.

### 2. CORS configuration is wide open (Medium)
`CORS(app)` in `app.py:21` allows all origins, methods, and headers. For a production legal research tool, this should be restricted to known frontend origins.

**Suggested fix:** `CORS(app, origins=["https://your-frontend-domain.com"], supports_credentials=True)`

### 3. No dedicated search-only endpoint (Low)
Retrieval without LLM requires `POST /api/v1/ask?use_llm=false`. This is non-obvious — a separate `GET /api/v1/search` endpoint would be cleaner. The current approach also requires a JWT for simple searches, which may be too restrictive for public access.

### 4. MMR vector cache is unbounded (Low)
`Reranker._vector_cache` stores TF vectors for every document ever accessed during the process lifetime. For 700 documents this is negligible (~50KB), but if the corpus grows significantly, the cache has no eviction policy.

### 5. Article lookup couples RAGRepository to SearchEngine (Medium)
`RAGRepository._build_article_lookup()` accesses `self.retrieval.engine.documents` to build the article lookup. This means:
- RAGRepository depends on RetrievalWorkflow having an `.engine` attribute
- The retrieval engine must have a `.documents` list
- If the retrieval pipeline switches to an external service, article lookup would break

**Suggested fix:** Inject the document list into RAGRepository directly, or load it from the same source as the engine.

### 6. Token_version check has a silent skip when DB is down (Low)
The `_get_user` function in `decorators.py` returns `None` if the database is unreachable. The decorator then skips the `token_version` check — the JWT is validated (signature + expiry) but version check is bypassed. This means a logged-out user's JWT remains valid until expiry if MongoDB is temporarily down. This is a deliberate tradeoff (uptime over invalidation precision) but should be documented.

---

## Technical Debt

| Debt | Location | Severity | Effort to Fix |
|------|----------|----------|---------------|
| Async def with sync I/O | `message_service.py`, `article_service.py` | Medium | 1 hour (remove `async def`) |
| `responses.txt` in preprocessing | `preprocessing_scripts/` | Low | 5 min (delete or .gitignore) |
| Unused CSS | `frontend/src/App.css` (~150 lines) | Low | 10 min (delete) |
| Unused npm dep (`pptxgenjs`) | `frontend/package.json` | Low | 5 min (remove) |
| UTF-16 `requirements.txt` | `backend/requirements.txt` | Low | 5 min (re-save as UTF-8) |
| No admin blueprint | Admin routes exist in `UserService` but no HTTP endpoints | Medium | 2 hours (blueprint + controller) |
| Hardcoded paths in `qa_service.py` | `_DEFAULT_DOCS_PATH` etc. | Low | Use relative paths from module location |

---

## Scalability

### Current state
- Single Flask process with `threaded=True`
- All data in memory (~700 Documents, 3 indexes in dicts)
- MongoDB handles persistence (users, messages, articles)
- Concurrent requests are limited by Python's GIL

### Bottlenecks
1. **MMR computation**: O(r²·t) per query. At 50 concurrent queries, each computing MMR on 50 results, this becomes noticeable (~2,500 iterations × cosine sims).
2. **Ollama single-process inference**: Ollama serves one request at a time per model (unless using vLLM or similar). Concurrent LLM requests queue.
3. **In-memory indexes**: All indexes must fit in RAM. For 700 docs this is fine, but if the corpus grows to 70,000 documents, the indexes (~500MB) plus TF vectors could stress a single process.

### Scaling strategies
1. **Read replicas for MongoDB** — messages and articles are read-heavy, especially chat history.
2. **Separate Ollama hosts** — multiple Ollama instances behind a load balancer for concurrent LLM inference.
3. **Vector index offload** — for large corpora, move TF index to a document database or an embedded key-value store (e.g., LMDB).
4. **Stateless Flask** — the only in-process state is the engine (loaded from JSON at startup). Horizontal scaling with a load balancer is straightforward: each process loads its own engine copy (~50MB RAM).

---

## Maintainability

### Good:
- The two-processor architecture (BM25 vs proximity) is well-documented and makes the code easy to reason about
- Each file has a clear, single responsibility
- The standalone `rag_workflow.py` demo is useful for testing without the Flask server
- Consistent error-return patterns in services (`{"success": bool, "error": str, "data": ...}`)
- No clever metaprogramming, decorators (except JWT), or dynamic dispatch

### Needs improvement:
- Tuple destructuring by position in `_score_document` / `_format_results` — a namedtuple would be more readable
- Some methods have 10+ parameters with no grouping (e.g., `ArticleService.create_article` with 16 parameters)
- No `__init__.py` exports for `src/core` — consumers import directly from modules
- The `_clean_body` regex in `rag_repository.py` depends on the exact output format of `flatten_constitution.py` — a format change breaks silently

---

## Testing Quality

**Current state:** Partial pytest suite at `backend/temp/tests/`.

### What's tested:
- `rag_workflow.py` standalone demo (manual)
- Basic API endpoints (via Postman collection in `postman/`)

### What's not tested:
- **Unit tests for IR engine:** `BM25Scorer`, `ProximityScorer`, `SearchEngine`, `Reranker` — none of these have automated unit tests. Given that they contain the most complex algorithms in the system (BM25 math, MMR iteration, TF vector computation), this is the highest-priority testing gap.
- **Integration tests with MongoDB:** No automated tests for `UserService`, `MessageService`, `ArticleService`.
- **Frontend tests:** Not tested.
- **Regression tests:** No test suite that runs on every commit.

### Suggestions:
1. Add pytest tests for `BM25Scorer.score()` with known inputs/outputs.
2. Add pytest tests for `ProximityScorer` with a small positional index.
3. Add pytest tests for `Reranker` with synthetic results — test RRF, MMR, and boost independently.
4. Add a test for `promote_to_articles` with a small corpus.
5. Add integration test for the `/ask` endpoint using a test client with mocked retrieval.

---

## Coupling

| From | To | Strength | Notes |
|------|----|----------|-------|
| `QAService` | `RAGWorkflow` | Tight (module-level global) | Single initialization at startup, global variable |
| `RAGRepository` | `RetrievalWorkflow.engine.documents` | Tight (attribute access) | Article lookup traverses engine.documents |
| `api_controller` | `QAService` | Loose (static methods) | Controllers don't instantiate services |
| `auth_controller` | `UserService` | Loose (static methods) | Standard service call |
| `Reranker` | `BM25Scorer.tf_index` | Loose (constructor injection) | Could reuse any TF-like dict |
| `SearchEngine` | `BM25Scorer`, `ProximityScorer` | Loose (constructor injection) | Scorers are swappable |
| `Frontend` | Backend API | Loose (REST + SSE) | Standard HTTP contract |

The overall coupling is **well-managed**. The IR engine is the most decoupled part — it could be extracted into a standalone library. The tightest coupling is between RAGRepository and RetrievalWorkflow's internal `.engine.documents`.

---

## Cohesion

- **High cohesion** in `src/core/`: Each class does exactly one thing (BM25 scoring, proximity scoring, search orchestration, reranking). Methods within each class operate on the same data.
- **High cohesion** in `src/llm/`: `RAGRepository` owns all LLM data access, `RAGFormatter` owns all string formatting, `RAGWorkflow` owns orchestration.
- **Medium cohesion** in `api_controller.py`: Handles Q&A endpoints AND message CRUD endpoints. These could be split into separate controllers.
- **Medium cohesion** in `user_service.py`: CRUD + authentication + JWT generation. Authentication could be separated from CRUD.

---

## Summary

### What to fix before release
1. Async def → sync in message/article services (easy, misleading)
2. Restrict CORS origins (easy, security)
3. Add unit tests for the IR engine core algorithms (medium, risk mitigation)

### What to fix after release
4. Add a dedicated `/api/v1/search` endpoint (medium)
5. Inject documents into RAGRepository instead of accessing `.engine.documents` (medium)
6. Replace tuple destructuring with namedtuples in `_score_document` (low)
7. Remove unused CSS, deps, and clean up `responses.txt` (low)
8. Admin blueprint for admin API routes (medium)
9. Normalize `requirements.txt` to UTF-8 (low)

### What not to change
- The two-processor architecture — it's the system's most important design insight
- Eager initialization with module-global workflow — keeps response times predictable
- Pure-Python math for ranking — avoids ML dependency issues
- Graceful degradation at every level — production-quality resilience
