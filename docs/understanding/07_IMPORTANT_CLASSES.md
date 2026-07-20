# Important Classes & Modules

Ranked by architectural importance (not code volume).

---

### 1. `RAGWorkflow` — `backend/src/llm/rag_workflow.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Central Q&A orchestrator — retrieves articles, calls LLM, assembles response |
| **Collaborators** | `RAGRepository`, `RAGFormatter` |
| **Why it exists** | Single entry point that both `answer_query()` and `answer_query_streaming()` delegate to. Owns the decision matrix (LLM on/off, error recovery). |
| **Design pattern** | **Facade** — exposes `ask()` and `ask_streaming()` that hide retrieval, promotion, prompt building, and LLM retry |
| **Complexity** | 6/10 — branching logic across LLM availability states |
| **Used by** | Every Q&A request — `QAService.answer_query()` and `answer_query_streaming()` |

---

### 2. `SearchEngine` — `backend/src/core/search_engine.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Multi-signal retrieval: BM25 + title boost + proximity scoring → top-k candidates |
| **Collaborators** | `BM25Scorer`, `ProximityScorer`, `TextProcessor` (×2), `QueryExpander`, `Document` |
| **Why it exists** | This is the heart of the IR engine. Implements the entire Phase 1 retrieval pipeline. Pure domain logic — zero framework dependencies. |
| **Design pattern** | **Strategy** — scoring signals are injected as separate objects; **Template Method** — `search()` defines the pipeline skeleton |
| **Complexity** | 7/10 — orchestrates 3 scoring signals, synonym expansion, candidate generation |
| **Used by** | `RetrievalWorkflow.retrieve()` on every query |

---

### 3. `RAGRepository` — `backend/src/llm/rag_repository.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Bridges retrieval + LLM worlds. Owns Ollama client, connectivity checks, retry logic, article lookup, and context truncation. |
| **Collaborators** | `RetrievalWorkflow`, `ollama.Client` |
| **Why it exists** | Separates LLM concerns (client management, retry, connectivity caching) from both the retrieval engine and the workflow orchestrator. |
| **Design pattern** | **Repository** — abstracts the data source (LLM + retrieval) behind a uniform interface |
| **Complexity** | 8/10 — manages Ollama client lifecycle, retry loop, API version variance in model list responses, article lookup construction |
| **Used by** | `RAGWorkflow` on every LLM-involved request |

---

### 4. `Reranker` — `backend/src/core/reranker.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Three-stage reranking: RRF signal fusion → MMR diversity → rule-based boost |
| **Collaborators** | `BM25Scorer.tf_index` (via constructor — for cosine similarity) |
| **Why it exists** | Phase 2 of retrieval. Raw SearchEngine results are high-recall; Reranker adds precision and diversity without ML. Pure math — zero imports beyond `math`. |
| **Design pattern** | **Pipeline** — three composable stages (`_rrf_fuse`, `_mmr_diversify`, `_apply_boost`) with a single public `rerank()` entry point |
| **Complexity** | 9/10 — MMR requires per-request O(n²) cosine similarity computations on sparse TF vectors; the vector cache adds tricky state management |
| **Used by** | `RetrievalWorkflow.retrieve()` on every query |

---

### 5. `QAService` — `backend/services/qa_service.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Application service that owns pipeline initialization and persistence. Exposes `answer_query()` and `persist_message()`. |
| **Collaborators** | `RAGWorkflow`, `ArticleService`, `MessageService`, `EngineFactory`, `Reranker` |
| **Why it exists** | Boundary between Flask controllers and the domain layer. Also holds the module-global `_workflow` singleton, making initialization explicit. |
| **Design pattern** | **Facade** — hides the entire pipeline assembly behind static methods; **Singleton** (for `_workflow` global) |
| **Complexity** | 4/10 — mostly delegation and wiring |
| **Used by** | `api_controller` on every Q&A request |

---

### 6. `EngineFactory` — `backend/src/core/engine_factory.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Assembles a fully-wired `SearchEngine` from disk artifacts (4 JSON files + synonyms) |
| **Collaborators** | All `src.core` modules — `Document`, `TextProcessor`, `BM25Scorer`, `ProximityScorer`, `SearchEngine`, `QueryExpander` |
| **Why it exists** | Encapsulates the complex construction logic. Without it, callers would need to load 4 JSON files, create 2 TextProcessors, 2 scorers, and wire a SearchEngine manually. |
| **Design pattern** | **Factory** (static) — the purest form of Factory Method in the codebase |
| **Complexity** | 3/10 — linear assembly with error handling for missing files |
| **Used by** | Called once at startup by `init_workflow()`, and by the standalone `rag_workflow.py` demo |

---

### 7. `BM25Scorer` — `backend/src/core/bm25_scorer.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Compute BM25 scores and identify matched terms for a document |
| **Collaborators** | None (pure calculation) |
| **Why it exists** | The primary ranking algorithm. `k1=1.5`, `b=1.0` (full length normalization — unusual but intentional for legal documents of varying length). |
| **Design pattern** | **Strategy** — the BM25 algorithm is encapsulated behind `score()` / `idf()` / `matched_terms()` |
| **Complexity** | 3/10 — standard BM25 formula with edge-case guards (df=0, doc_len=0, tf=0) |
| **Used by** | `SearchEngine._score_document()` for every candidate on every query |

---

### 8. `RetrievalWorkflow` — `backend/src/workflows/retrieval_workflow.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Composes SearchEngine + Reranker into a single `retrieve(query)` → `list[dict]` step |
| **Collaborators** | `SearchEngine`, `Reranker` |
| **Why it exists** | Defines the canonical retrieval pipeline: recall_k=50 → search → rerank → top_k=8. This is the unit reused by both `RAGRepository` and any future standalone search path. |
| **Design pattern** | **Facade** — hides the two-phase pipeline behind `retrieve()` |
| **Complexity** | 2/10 — thin composition |
| **Used by** | `RAGRepository.retrieve()` on every query |

---

### 9. `TextProcessor` — `backend/src/core/text_processor.py`

| Field | Value |
|-------|-------|
| **Responsibility** | NLP pipeline: normalize → optionally lemmatize → optionally remove stopwords |
| **Collaborators** | `CONTRACTIONS_MAP` (constants), `STOPWORDS` (constants), spaCy pipeline |
| **Why it exists** | Two instances exist at runtime (BM25 processor and proximity processor) with different configurations. Centralizes text normalization so all tokenization decisions live in one file. |
| **Design pattern** | **Strategy** — two configured instances with different lemmatize/stopword settings; **Lazy Initialization** — spaCy pipeline loaded on first `process_text()` call |
| **Complexity** | 4/10 — regex contraction expansion, spaCy fallback logic |
| **Used by** | `SearchEngine` (both processors), `IndexBuilder`, `EngineFactory` |

---

### 10. `ProximityScorer` — `backend/src/core/proximity.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Score document relevance by how close query term pairs appear in the positional index |
| **Collaborators** | None (pure algorithm with injected positional index) |
| **Why it exists** | Adds term-proximity signal that BM25 cannot capture. "right to education" and "education right" get different proximity scores even though BM25 treats them identically. |
| **Design pattern** | **Strategy** — `score()` takes a list of pairs and returns a float; pair generation heuristic (all-pairs ≤5 tokens, adjacent only >5) is encapsulated in `generate_query_pairs()` |
| **Complexity** | 5/10 — two-pointer minimum-distance algorithm, quadratic inverse score formula, max_window cutoff |
| **Used by** | `SearchEngine._score_document()` for every candidate on every query |

---

### 11. `RAGFormatter` — `backend/src/llm/rag_formatter.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Build LLM prompts: context formatting, system instructions, user query wrapper |
| **Collaborators** | None (pure string builder) |
| **Why it exists** | Separates prompt engineering from orchestration logic. All LLM instruction changes happen here without touching retrieval or controller code. |
| **Design pattern** | Builder — constructs multi-part prompts via dedicated methods |
| **Complexity** | 2/10 — string concatenation and template logic |
| **Used by** | `RAGWorkflow.ask()` and `ask_streaming()` |

---

### 12. `QueryExpander` — `backend/src/core/query_expander.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Expand query tokens with 44 synonym groups for improved recall |
| **Collaborators** | None (loaded from `data/synonyms.json`) |
| **Why it exists** | Legal terminology has high variance: "arrest/detention/custody", "right/entitlement/prerogative". Synonym expansion bridges the gap between user vocabulary and constitutional text vocabulary. |
| **Design pattern** | Decorator — wraps token list and returns an expanded version |
| **Complexity** | 4/10 — multi-word phrase detection, group-based lookup construction, deduplication |
| **Used by** | `SearchEngine.search()` for every query (if synonyms_path was provided at construction) |

---

### 13. `User` (Model) — `backend/models/user_model.py`

| Field | Value |
|-------|-------|
| **Responsibility** | MongoDB document model for user accounts. Handles password hashing and JSON serialization. |
| **Collaborators** | mongoengine, bcrypt |
| **Why it exists** | The authentication user. Every Q&A request requires a valid User with matching token_version. |
| **Design pattern** | **Active Record** (mongoengine Document) — combines data and persistence in one class |
| **Complexity** | 2/10 — standard user model with password methods |
| **Used by** | `UserService`, `auth_controller`, `decorators.py`, `MessageService` |

---

### 14. `Message` (Model) — `backend/models/message_model.py`

| Field | Value |
|-------|-------|
| **Responsibility** | MongoDB document model for Q&A exchanges with article references |
| **Collaborators** | mongoengine, `User` (reference), `ReferencedArticle` (reference list) |
| **Why it exists** | Persists every Q&A exchange so users can browse history. Links users to articles. |
| **Design pattern** | **Active Record** — combines data and persistence |
| **Complexity** | 2/10 — references + timestamps |
| **Used by** | `MessageService` |

---

### 15. `ReferencedArticle` (Model) — `backend/models/referenced_article_model.py`

| Field | Value |
|-------|-------|
| **Responsibility** | MongoDB document model for a constitutional provision snapshot at query time |
| **Collaborators** | mongoengine |
| **Why it exists** | Freezes the retrieval state so historical messages remain accurate even if the ranking algorithm changes. Also stores matched terms for frontend highlighting. |
| **Design pattern** | **Active Record** — combines data and persistence |
| **Complexity** | 2/10 — 22 fields, body-cleaning regex |
| **Used by** | `ArticleService`, `MessageService` |

---

### 16. `IndexBuilder` — `backend/src/core/index_builder.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Build TF index, positional index, and document statistics from a flat document list |
| **Collaborators** | `Document`, `TextProcessor` |
| **Why it exists** | Offline pipeline. Run once during ingestion to produce the three JSON indexes that `EngineFactory` needs at startup. |
| **Design pattern** | **Builder** — `build_all_indexes()` returns three indexes at once |
| **Complexity** | 3/10 — multi-pass counting |
| **Used by** | `IngestionWorkflow` (offline), never at request time |

---

### 17. `Database` — `backend/config/db_connect.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Singleton MongoDB connection manager |
| **Collaborators** | mongoengine |
| **Why it exists** | Ensures exactly one connection pool is created per process. Fail-fast on startup if MongoDB is unreachable. |
| **Design pattern** | **Singleton** — `_instance` class variable with `__new__` override |
| **Complexity** | 1/10 — connection wrapper |
| **Used by** | Called once at startup in `create_app()` |

---

### 18. `token_required` (Decorator) — `backend/controllers/decorators.py`

| Field | Value |
|-------|-------|
| **Responsibility** | JWT authentication gate — extracts token, validates signature, checks token_version |
| **Collaborators** | PyJWT, `User` (model) |
| **Why it exists** | Centralizes all auth logic so controllers don't duplicate it. Supports Bearer header + cookie fallback. |
| **Design pattern** | **Decorator** — wraps route handlers with pre-request validation |
| **Complexity** | 4/10 — multi-source token extraction, token_version invalidation, DB-availability fallback |
| **Used by** | All protected routes in `api_routes.py` and `auth_routes.py` |

---

### 19. `Document` (Dataclass) — `backend/src/core/document.py`

| Field | Value |
|-------|-------|
| **Responsibility** | Typed data container for a single row in the flattened constitution corpus |
| **Collaborators** | None (plain dataclass) |
| **Why it exists** | Gives the IR engine a consistent typed representation of provisions. All 700+ corpus entries are `Document` instances. |
| **Design pattern** | **DTO / Data Transfer Object** — pure data with no behavior |
| **Complexity** | 1/10 — 14 fields, no methods |
| **Used by** | `EngineFactory`, `SearchEngine`, `IndexBuilder`, `IngestionWorkflow` — every class that touches corpus data |

---

### 20. `RAGFormatter` (Frontend: `ui/` Primitives as a Group)

| Field | Value |
|-------|-------|
| **Responsibility** | 9 reusable UI primitives: Button, Input, Toggle, Card, Alert, Badge, Spinner, Pagination, Dialog |
| **Collaborators** | React, Tailwind CSS |
| **Why it exists** | Consistent, accessible presentation layer. Every page and feature component delegates visual rendering to these primitives. |
| **Design pattern** | **Composite** — pages compose feature components which compose primitives |
| **Complexity** | 2/10 each — pure presentational components with variant/size props |
| **Used by** | Every page in the frontend |

---

## Honorable Mentions

| Module | Rank | Why It Didn't Make Top 20 |
|--------|:----:|---------------------------|
| `UserService` | 21 | Thin CRUD wrapper over User model |
| `MessageService` | 22 | Same — CRUD with pagination |
| `ArticleService` | 23 | Same — upsert by doc_id |
| `IngestionWorkflow` | 24 | Offline-only, never runs at request time |
| `AuthProvider` (frontend) | 25 | Important but simpler than backend classes |
| `useAskStream` (hook) | 26 | SSE streaming wrapper — clever but small |
| `FlattenConstitution` (script) | 27 | Offline preprocessing, not runtime |
