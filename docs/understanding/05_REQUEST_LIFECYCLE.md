# Request Lifecycle — `POST /api/v1/ask` (with LLM)

## Representative Request

```
POST /api/v1/ask
Authorization: Bearer <JWT>
Content-Type: application/json

{"query": "What are the fundamental rights?", "use_llm": true}
```

---

## Lifecycle Map

```
Client
  │
  │ POST /api/v1/ask  (JWT Bearer + JSON body)
  ▼
Flask Router ──────────────────────────────────────────────────────────┐
  │                                                                    │
  │ 1. ┌─── @token_required (decorator) ───┐                          │
  │    │  Extract Bearer token              │                          │
  │    │  jwt.decode(token, JWT_SECRET)     │                          │
  │    │  User lookup → token_version check │  ← MongoDB               │
  │    │  request.user = payload            │                          │
  │    └────────────────────────────────────┘                          │
  │                                                                    │
  │ 2. api_routes.py → ask_route() → ask()                            │
  ▼                                                                    │
api_controller.py : ask() ────────────────────────────────────────────┤
  │                                                                    │
  │ _parse_ask_request() → validate JSON, query ≤ 500 chars           │
  │                                                                    │
  │ QAService.answer_query(query, use_llm=True) ────────────────────┐ │
  ▼                                                                  │ │
qa_service.py : answer_query()                                      │ │
  │                                                                  │ │
  │ _get_workflow() → module-global _workflow (RAGWorkflow)         │ │
  │                                                                  │ │
  │ workflow.ask(query, use_llm=True) ─────────────────────────┐     │ │
  ▼                                                             │     │ │
rag_workflow.py : RAGWorkflow.ask()                             │     │ │
  │                                                             │     │ │
  │ 1. _prepare_articles(query)                                 │     │ │
  │    ├── repo.retrieve(query, top_k=8) ────────────────┐      │     │ │
  │    │   ↓                                              │      │     │ │
  │    │   rag_repository.py : RAGRepository.retrieve()    │      │     │ │
  │    │    └── retrieval_workflow.retrieve(query) ──────┐ │      │     │ │
  │    │        ↓                                        │ │      │     │ │
  │    │        retrieval_workflow.py : retrieve()        │ │      │     │ │
  │    │         ├── engine.search(query, top_k=50) ───┐ │ │      │     │ │
  │    │         │   ↓                                  │ │ │      │     │ │
  │    │         │   search_engine.py : SearchEngine    │ │ │      │     │ │
  │    │         │     .search()                       │ │ │      │     │ │
  │    │         │    ├── TextProcessor.process (BM25)  │ │ │      │     │ │
  │    │         │    │   └── spaCy lemmatization       │ │ │      │     │ │
  │    │         │    ├── synonym_expander.expand()     │ │ │      │     │ │
  │    │         │    ├── _generate_candidates()        │ │ │      │     │ │
  │    │         │    ├── BM25Scorer.score()            │ │ │      │     │ │
  │    │         │    ├── title_boost computation       │ │ │      │     │ │
  │    │         │    ├── ProximityScorer.score()       │ │ │      │     │ │
  │    │         │    └── hybrid scoring + sort         │ │ │      │     │ │
  │    │         │                                    ←───┤ │      │     │ │
  │    │         │   Returns top 30 scored documents    ┘ │ │      │     │ │
  │    │         │                                        │ │      │     │ │
  │    │         └── reranker.rerank(results, top_k=8) ─┐ │ │      │     │ │
  │    │             ↓                                   │ │ │      │     │ │
  │    │             reranker.py : Reranker.rerank()      │ │ │      │     │ │
  │    │              ├── _rrf_fuse() — RRF fusion        │ │ │      │     │ │
  │    │              │   (k=60, BM25+prox+title ranks)  │ │ │      │     │ │
  │    │              ├── _mmr_diversify() — MMR (λ=0.5) │ │ │      │     │ │
  │    │              └── _apply_boost() — part/level     │ │ │      │     │ │
  │    │              Returns top 8 results             ←───┤ │      │     │ │
  │    │                                                ←────┤ │      │     │ │
  │    └── repo.promote_to_articles(raw_results)           │ │      │     │ │
  │        : RAGRepository.promote_to_articles()            │ │      │     │ │
  │         ├── Group by article_no                        │ │      │     │ │
  │         ├── Merge clause/sub-clause → full article     │ │      │     │ │
  │         ├── Deduplicate (first occurrence wins)        │ │      │     │ │
  │         └── Track matched clauses                     │ │      │     │ │
  │                                                       │ │      │     │ │
  │ 2. Ollama connectivity check ─────────────────────────┘ │      │     │ │
  │    repo.check_ollama_connection()                        │      │     │ │
  │     ├── client.list() (HTTP call to Ollama)              │      │     │ │
  │     └── cached per process lifetime                     │      │     │ │
  │                                                         │      │     │ │
  │ 3. Model availability check                              │      │     │ │
  │    repo.check_model_availability()                       │      │     │ │
  │     └── "qwen3:8b" in cached model list                  │      │     │ │
  │                                                         │      │     │ │
  │ 4. LLM call                                              │      │     │ │
  │    ├── formatter.format_context(articles)               │      │     │ │
  │    ├── formatter.build_system_prompt()                  │      │     │ │
  │    ├── formatter.build_user_prompt(query, context)      │      │     │ │
  │    └── repo.call_llm(messages, stream=False)            │      │     │ │
  │         └── client.chat(model, messages,                │      │     │ │
  │             keep_alive="30m", num_ctx=4096)             │      │     │ │
  │              └── 3-attempt retry loop (0.5s delay)      │      │     │ │
  │                                                        └──────┘     │ │
  │                                                                      │ │
  │ 5. Assemble response: query + articles + response + citations       │ │
  │    + ollama_status                                                  │ │
  │                                                                     │ │
  │ Return result dict ←────────────────────────────────────────────────┘ │
  │                                                                       │
  │ status=200                                                            │
  │                                                                       │
  │ 6. QAService.persist_message(user_id, query, payload) ────────────┐  │
  ▼                                                                     │  │
api_controller.py : persist step                                        │  │
  │                                                                     │  │
  │ 7. For each article in payload:                                     │  │
  │    ArticleService.create_article(...)                                │  │
  │     ├── ReferencedArticle.objects(doc_id=...).first()                │  │
  │     ├── Upsert → existing.save() or new article.save()              │  │
  │     └── Return ObjectId                                             │  │
  │                                                                     │  │
  │ 8. MessageService.create_message(user_id, query, answer, articles)  │  │
  │     ├── User.objects.get(id=user_id)                                │  │
  │     ├── ReferencedArticle.objects.get(id=...) for each article ref  │  │
  │     ├── Message(query, answer, user, articles).save()              │  │
  │     └── Return success                                              │  │
  │                                                                     │  │
  │ Persist failures → logged, never break response                     │  │
  │                                                                     │  │
  │ 9. jsonify(payload) ←───────────────────────────────────────────────┘  │
  ▼                                                                         │
Client receives HTTP 200                                                    │
  {                                                                         │
    "query": "What are the fundamental rights?",                            │
    "response": "The Constitution guarantees... (Article 16...) ...",       │
    "articles": [... 8 article dicts ...],                                  │
    "citations": [... 8 citation objects ...],                              │
    "ollama_status": { "connected": true, "model": "qwen3:8b",             │
                       "model_available": true }                           │
  }                                                                         │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Step-by-Step Trace

### Phase 1 — Authentication (`controllers/decorators.py:28-68`)

**File:** `backend/controllers/decorators.py`
**Function:** `token_required(f)` — decorator factory, returns `decorated()`

| Step | File:Line | What Happens |
|------|-----------|--------------|
| 1a | `decorators.py:31` | `request.headers.get('Authorization')` — reads `Authorization: Bearer <jwt>` |
| 1b | `decorators.py:34-35` | Strips `"Bearer "` prefix to extract the raw JWT string |
| 1c | `decorators.py:36-37` | **Fallback:** if no header, reads `request.cookies.get('token')` |
| 1d | `decorators.py:39-40` | If no token found anywhere → 401 `{"error": "Token is missing!"}` |
| 1e | `decorators.py:42-43` | Reads `JWT_SECRET` from environment → early 500 if unset |
| 1f | `decorators.py:47` | `jwt.decode(token, JWT_SECRET, algorithms=['HS256'])` — verifies signature + expiry (12h) |
| 1g | `decorators.py:49` | `_get_user(payload['user_id'])` — queries `User.objects(id=user_id).first()` via MongoDB |
| 1h | `decorators.py:53-55` | **Token version check:** if `payload.token_version < user.token_version` → 401 (logout invalidates all prior JWTs) |
| 1i | `decorators.py:57` | `request.user = payload` — attaches decoded JWT payload to Flask request context for downstream use |
| 1j | `decorators.py:58-64` | Catches `ExpiredSignatureError` (→ 401), `InvalidTokenError` (→ 401), other exceptions (→ 500) |

**Why:** Every `/ask` request requires authentication. The decorator validates the JWT and attaches the user identity to the request context.

**MongoDB hit:** One query to `users` collection for token_version check.

---

### Phase 2 — Route Matching (`routes/api_routes.py:28-31`)

```
File: backend/routes/api_routes.py
Route: @api_bp.route("/api/v1/ask", methods=["POST"])
Handler: ask_route() → ask()
```

Flask matches the `POST /api/v1/ask` path against registered blueprints. The `api_bp` blueprint was registered at startup with no prefix, so `/api/v1/ask` matches line 28.

`ask_route()` simply calls `ask()` — a thin passthrough.

---

### Phase 3 — Request Validation (`controllers/api_controller.py:40-87`)

**File:** `backend/controllers/api_controller.py`
**Function:** `ask()` (line 62)

| Step | File:Line | What Happens |
|------|-----------|--------------|
| 3a | `api_controller.py:65` | `_parse_ask_request()` validates: JSON content-type (line 42), parseable JSON (line 45-47), `query` is a string (line 53), query ≤ 500 chars (line 56-57) |
| 3b | `api_controller.py:70` | Reads `use_llm` from body, defaults to `False` |
| 3c | `api_controller.py:73` | Calls `QAService.answer_query(query, use_llm=True)` — the main orchestration |

**Input:** `request` object (Flask) with `query="What are the fundamental rights?"`, `use_llm=true`
**Output:** Tuple `(payload dict, status_code int)`
**Failure modes:** Bad content-type → 400, missing query → 400, too long → 400

---

### Phase 4 — Service Orchestration (`services/qa_service.py:38-87`)

**File:** `backend/services/qa_service.py`
**Function:** `QAService.answer_query()` (line 84)

```python
@staticmethod
def answer_query(query: str, use_llm: bool = False) -> tuple[dict, int]:
    workflow = QAService._get_workflow()
    return workflow.ask(query, use_llm=use_llm), 200
```

- Retrieves the module-global `_workflow` (RAGWorkflow instance assembled at startup)
- Delegates to `RAGWorkflow.ask()`
- Always returns status 200 (errors are encoded in the response body for graceful degradation)

**Why:** QAService is a thin passthrough. It was originally designed to hold the pipeline initialization and persistence. At request time it simply hands control to the workflow.

---

### Phase 5 — RAG Workflow (`src/llm/rag_workflow.py:53-120`)

**File:** `backend/src/llm/rag_workflow.py`
**Function:** `RAGWorkflow.ask()` (line 53)

#### 5a. Article Retrieval + Promotion (`rag_workflow.py:45-51`)

`_prepare_articles(query)`:
1. `repo.retrieve(query, top_k=8)` — delegates to retrieval pipeline (Phase 6 below)
2. `repo.promote_to_articles(retrieved)` — merges clause-level results into full articles (Phase 7 below)
3. Copies `full_text` ↔ `text` for downstream formatting

#### 5b. LLM Decision Matrix (`rag_workflow.py:70-119`)

| Condition | Code Path | Output |
|-----------|-----------|--------|
| `use_llm=False` | Line 70-71 | Returns `{query, articles}` immediately |
| Ollama unreachable | Lines 73-80 | Returns `{query, articles, ollama_status: {connected: false}}` |
| Model missing | Lines 82-92 | Returns `{query, articles, ollama_status: {connected: true, model_available: false}}` |
| LLM succeeds | Lines 94-109 | Returns `{query, articles, response, citations, ollama_status}` |
| LLM fails after retries | Lines 110-113 | Returns `{query, articles, response (error text), error}` |

For the happy path with `use_llm=true`:

1. **Check connectivity** — `repo.check_ollama_connection()` (lazy, cached per process)
2. **Check model availability** — `repo.check_model_availability()` (cached model list)
3. **Format prompt** — `rag_formatter.py`:
   - `format_context(promoted_articles)` — builds a string with citation + title + text + score per article
   - `build_system_prompt()` — returns strict-grounding instructions
   - `build_user_prompt(query, context)` — wraps query + context in final prompt
4. **Call LLM** — `repo.call_llm(messages, stream=False)` with 3-attempt retry
5. **Assemble response** — extracts `response.message.content`, builds citations list

---

### Phase 6 — Retrieval Pipeline (deep dive)

This is the most computationally intensive path.

#### 6a. `RAGRepository.retrieve(query, top_k=8)` — `rag_repository.py:213-220`

Straight delegation: calls `self.retrieval.retrieve(query, top_k)`.

#### 6b. `RetrievalWorkflow.retrieve(query, top_k=8)` — `retrieval_workflow.py:23-46`

```python
def retrieve(self, query, top_k=None, boost_rules=None):
    recall_k = self.default_recall_k          # 50
    final_k = top_k or self.default_top_k      # 8

    initial_results = self.engine.search(query, top_k=recall_k)  # Step 6c
    if not initial_results:
        return []

    return self.reranker.rerank(initial_results, top_k=final_k,   # Step 6d
                                boost_rules=boost_rules)
```

**Why two phases?** Phase 1 (SearchEngine) casts a wide net for recall. Phase 2 (Reranker) refines for precision and diversity.

#### 6c. `SearchEngine.search(query, top_k=50)` — `search_engine.py:79-127`

```
Input:  "What are the fundamental rights?"
Output: 30 scored document dicts
```

| Step | Function | What Happens |
|------|----------|--------------|
| 6c.1 | `bm25_processor.process_text(query)` | Lemmatize + stopword removal → `["fundamental", "right"]` |
| 6c.2 | `synonym_expander.expand(bm25_tokens, raw_query)` | Expands to include synonyms like `["fundamental", "right", "entitlement", "prerogative", ...]` |
| 6c.3 | `proximity_processor.process_text(query)` | No lemmatization, keeps stopwords → `["what", "are", "the", "fundamental", "rights"]` |
| 6c.4 | `ProximityScorer.generate_query_pairs(raw_tokens)` | 5 tokens ≤ 5 → all-pairs: 10 pairs (what-are, what-the, what-fundamental, ...) |
| 6c.5 | `_generate_candidates(bm25_tokens)` | Union of `tf_index[token].keys()` for each expanded token → set of doc IDs |
| 6c.6 | Loop: `_score_document(doc, ...)` for each candidate | BM25 + title_match_count × 5.0 + 1.0 × proximity_score |
| 6c.7 | Sort by `final_score` DESC, take top 50 | Returns 50 results → but `search_engine.py:127` takes `scored[:top_k]` where `top_k=50` (recall_k), so all candidates pass |

**Inside `_score_document`** (`search_engine.py:142-179`):

```
score = BM25(bm25_tokens, doc_id)
      + len(set(bm25_tokens) ∩ title_tokens[doc_id]) × 5.0
      + 1.0 × ProximityScorer.score(doc_id, query_pairs, max_window=30)
```

**BM25 formula** (`bm25_scorer.py:27-41`):
```
score = Σᵢ IDF(tᵢ) × tf(tᵢ,D)×(k₁+1) / (tf(tᵢ,D) + k₁×(1-b+b×|D|/avgdl))
where k₁=1.5, b=1.0
IDF(t) = ln((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
```

**Proximity formula** (`proximity.py:67-103`):
```
score = 1/n × Σₚ 1/(d(p)+1)²
for each pair p within max_window=30 tokens
d(p) = minimum ordered distance between term1 and term2
```

#### 6d. `Reranker.rerank(results, top_k=8)` — `reranker.py:164-180`

```
Input:  30 scored docs from SearchEngine
Output: 8 reranked docs
```

| Stage | Function | What Happens |
|-------|----------|--------------|
| 6d.1 | `_rrf_fuse()` | Computes 3 separate rankings (BM25, proximity, title-match), fuses via `RRF = Σ 1/(60 + rank)` |
| 6d.2 | Sort by RRF score DESC | Results reordered |
| 6d.3 | `_mmr_diversify()` | `λ=0.5`: picks highest RRF first, then iteratively selects candidates max `λ×score - (1-λ)×max_similarity` |
| 6d.4 | `_apply_boost()` | Multiplies `score × boost × part_rules[part_no] × level_rules[level]` |
| 6d.5 | `results[:top_k]` | Takes top 8 |

**Why RRF+MMR?** RRF combines three independent signals without tuning weights. MMR ensures diversity — the top-8 results won't all be from Part 3 (Fundamental Rights) even if the query is about rights.

---

### Phase 7 — Article Promotion (`rag_repository.py:175-208`)

**File:** `backend/src/llm/rag_repository.py`
**Function:** `promote_to_articles()`

The reranker returns individual document-level results (articles, clauses, sub-clauses). This function merges them into full articles:

1. **Scans results** to build `matched_clauses_per_article` — a dict of article_no → set of matched clause numbers
2. **Iterates results** (already sorted by score descending):
   - For each unique `article_no`, looks up the pre-built article text from `_article_lookup`
   - Adds matched clause tracking
   - Skips duplicate article_no entries (first occurrence keeps its score)
3. Returns deduplicated, full-article results

**Why:** Users want to see full articles, not fragments. Clauses are merged so the user reads complete provisions.

---

### Phase 8 — Persistence (`api_controller.py:76-77`)

**File:** `backend/controllers/api_controller.py`
**Function:** inline in `ask()` (line 76-77)

```python
if status_code == 200:
    user_id = request.user.get("user_id")
    QAService.persist_message(user_id, query, payload)
```

#### 8a. `QAService.persist_message()` — `qa_service.py:43-81`

```
File: backend/services/qa_service.py
```

For each article in `payload["articles"]`:

1. **`ArticleService.create_article(...)`** — `article_service.py:10-73`
   - Queries `ReferencedArticle.objects(doc_id=...).first()`
   - If exists → updates text, scores, matched terms, saves
   - If new → creates `ReferencedArticle(...).save()`
   - Returns `{success, data: {id: ObjectId}}`

2. **`MessageService.create_message(user_id, query, answer, article_ids)`** — `message_service.py:16-72`
   - `User.objects.get(id=user_id)` — resolves the user reference
   - `ReferencedArticle.objects.get(id=...)` for each article id — resolves article references
   - `Message(query, answer, user, articles).save()` — creates the message document

**Fire-and-forget:** All persistence failures are caught and logged. They never affect the HTTP response.

**Why:** Message persistence must never block the user from getting their answer. If MongoDB has a transient failure, the user still gets their results; the conversation is simply not recorded.

---

### Phase 9 — Response (`api_controller.py:84`)

```python
return jsonify(payload), status_code
```

**Response shape (success, with LLM):**

```json
{
  "query": "What are the fundamental rights?",
  "response": "The Constitution of Nepal guarantees several fundamental rights... (Part 3, Article 16)...",
  "articles": [
    {
      "doc_id": "31",
      "part_no": 3,
      "article_no": 31,
      "title": "Right relating to education",
      "citation": "Part 3, Article 31",
      "content": "(1) Every citizen shall have the right to access to education...",
      "text": "Part 3 Article 31\nRight relating to education\nClause 1...",
      "level": "article",
      "score": 8.47,
      "bm25_score": 6.12,
      "proximity_score": 2.35,
      "title_match_count": 2,
      "matched_terms": ["right", "education"],
      "exact_matched_terms": ["rights"],
      "boost_multiplier": 0.98,
      "matched_clauses": ["1", "2", "3"]
    },
    ...
  ],
  "citations": [
    {"article": "Part 3, Article 31", "title": "Right relating to education", "doc_id": "31"},
    ...
  ],
  "ollama_status": {
    "connected": true,
    "model": "qwen3:8b",
    "model_available": true
  }
}
```

**Content-Type:** `application/json`
**Status:** `200 OK` (errors are encoded in body, never 500 for LLM failures)

---

## Failure Mode Matrix

| Failure Point | Behavior | HTTP Status | User Sees |
|---------------|----------|:-----------:|-----------|
| Missing/invalid JWT | Decorator rejects | 401 | `{"error": "Token is missing!"}` |
| Bad JSON body | `_parse_ask_request()` | 400 | `{"error": "Invalid JSON payload."}` |
| Query > 500 chars | `_parse_ask_request()` | 400 | `{"error": "Query is too long..."}` |
| Search returns nothing | RAGWorkflow | 200 | `articles: []` |
| Ollama unreachable | `check_ollama_connection()` | 200 | `articles` + `ollama_status.connected=false` |
| Model missing | `check_model_availability()` | 200 | `articles` + `ollama_status.model_available=false` |
| LLM fails 3× retry | `call_llm()` catch | 200 | `response` (error text) + `error` field |
| Article persist fails | `ArticleService` catch | 200 | Answer intact; failure logged |
| Message persist fails | `MessageService` catch | 200 | Answer intact; failure logged |
| Unhandled exception | `ask()` outer try/except | 500 | `{"error": "An error occurred..."}` |
| MongoDB connection lost (mid-request) | `token_required` → `_get_user` | 401 | Token validation passes (skips version check), but downstream CRUD fails |

---

## Key Design Properties

- **Graceful degradation at every layer** — LLM, MongoDB, and search all have independent failure modes that degrade rather than crash
- **No locking or contention** — no shared mutable state during request processing; all pipeline objects are read-only after startup
- **Synchronous orchestration** — no async/await, no queue, no background jobs. Request-response is synchronous within the thread
- **Stateless IR engine** — `SearchEngine` and `Reranker` are pure computation with no side effects
- **Persistence is best-effort** — fire-and-forget after the response is computed
