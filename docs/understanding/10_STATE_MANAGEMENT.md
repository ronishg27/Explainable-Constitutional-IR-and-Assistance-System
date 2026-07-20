# State Management

---

## State Inventory

| State Type | Location | What It Stores | Lifetime |
|------------|----------|----------------|----------|
| **Database** | MongoDB `ECIRAS` | users, messages, referenced_articles | Permanent |
| **Global (module-level)** | `services/qa_service.py:_workflow` | Singleton RAGWorkflow instance | Process lifetime |
| **Global (module-level)** | `src/core/text_processor.py:_spacy_nlp` | spaCy NLP pipeline | Process lifetime |
| **Singleton (class)** | `config/db_connect.py:Database._instance` | MongoDB connection singleton | Process lifetime |
| **In-memory cache** | `src/core/reranker.py:_vector_cache` | Sparse TF vectors for MMR | Process lifetime |
| **In-memory cache** | `src/llm/rag_repository.py:_ollama_available` | Ollama connectivity status | Process lifetime (1st request) |
| **In-memory cache** | `src/llm/rag_repository.py:_available_models` | Ollama model list | Process lifetime (1st request) |
| **In-memory cache** | `src/llm/rag_repository.py:_article_lookup` | Pre-built article → text mapping | Process lifetime (startup) |
| **In-memory cache** | `src/llm/rag_repository.py:_clause_structure` | Pre-built clause structure mapping | Process lifetime (startup) |
| **HTTP** | JWT payload on `request.user` | Authenticated user identity | Per-request |
| **Local** | React `useState` | Query input, results, loading flags | Per-component mount |
| **Local** | React `useRef` | AbortController for streaming | Per-component mount |
| **Persistent (localStorage)** | Frontend `localStorage` | JWT token | Until logout or expiry |
| **Persistent (cookie)** | Frontend httpOnly cookie | JWT token (fallback) | Until logout or expiry |

---

## Database State (MongoDB — `ECIRAS`)

### Collection: `users`

| Field | Type | Mutability |
|-------|------|------------|
| `fullname` | String | Write-once (registration) |
| `email` | String | Write-once |
| `password_hash` | String | Write-once |
| `role` | Enum | Write-once |
| `token_version` | Int | **Incremented on every logout** |
| `created_at` | DateTime | Auto-set |
| `updated_at` | DateTime | Auto-updated on save |

### Collection: `messages`

| Field | Type | Mutability |
|-------|------|------------|
| `query` | String | Write-once |
| `answer` | String | Write-once |
| `user` | Reference | Write-once |
| `articles` | List\[Reference\] | Write-once |
| `created_at` | DateTime | Auto-set |
| `updated_at` | DateTime | Auto-updated on save |

### Collection: `referenced_articles`

| Field | Type | Mutability |
|-------|------|------------|
| `doc_id` | String | **Upsert key** — existing doc updated, new doc created |
| All score fields | Float | Updated on re-query with same `doc_id` |
| `matched_terms` | List\[String\] | Updated on re-query |
| Timestamps | DateTime | Auto-managed |

### Consistency Rules

- **Token version invalidation:** `token_version` is the sole source of truth for session validity. When a user logs out, `token_version` increments. All JWTs carry the version at issue time. On every protected request, the decorator compares `jwt.token_version` against `user.token_version`. If the DB version is higher, the JWT is rejected. This is a **version-based invalidation**, not a blacklist.
- **User deletion:** CASCADE-deletes all owned Messages (`reverse_delete_rule=2`).
- **Article deletion:** NULLIFIES the reference in Messages (`reverse_delete_rule=3`) — messages survive without the article data.
- **No transactions:** Each save is atomic, but there is no multi-document transaction. If the server crashes between `ArticleService.create_article()` and `MessageService.create_message()`, the orphan article documents remain. This is accepted — articles are immutable snapshots and orphan data has no user-facing impact.

---

## Global / Module-Level State

### `_workflow` — `services/qa_service.py:20`

```python
_workflow: Optional[RAGWorkflow] = None
```

- **Initialized:** Once at startup by `init_workflow()`
- **Accessed:** On every `/ask` and `/ask-stream` request via `_get_workflow()`
- **Mutability:** Read-only after initialization
- **Why global:** Avoids reconstructing the entire RAG pipeline (EngineFactory → SearchEngine → Reranker → RetrievalWorkflow → RAGRepository → RAGFormatter → RAGWorkflow) on every request. Startup takes ~1s; constructing per-request would make every query slow.

### `_spacy_nlp` — `src/core/text_processor.py:6`

```python
_spacy_nlp = None
```

- **Initialized:** Lazy — on first call to `get_spacy_pipeline()` (which happens during `EngineFactory.from_artifacts()` when title tokens are pre-processed)
- **Accessed:** By every `TextProcessor.process_text()` call
- **Mutability:** Read-only after initialization
- **Why global:** spaCy pipeline loading is expensive (~300ms) and memory-heavy (~50MB). One instance per process is the standard pattern.

---

## Singleton Pattern

### `Database` — `config/db_connect.py:7-14`

```python
class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

- **Thread safety:** Not guarded (`__new__` is not synchronized). In a multi-threaded WSGI server, two threads could pass the `None` check simultaneously and create two instances. In practice, `Database().connect()` is called once during startup (single-threaded), so this never races.
- **Connection pool:** `mongoengine.connect()` manages its own pool (`maxPoolSize=10`, `minPoolSize=2`). The `Database` singleton just ensures `connect()` is called exactly once.
- **Why singleton:** Prevents duplicate connection pools to the same database.

---

## In-Memory Caches

### `Reranker._vector_cache` — `src/core/reranker.py:22`

```python
self._vector_cache: dict[str, dict[str, int]] = {}
```

- **What:** Sparse BM25 TF vectors, keyed by `doc_id`. Built lazily on first `_get_tf_vector(doc_id)` call.
- **Size:** One dict per unique document seen during reranking. Each dict has entries only for terms present in that document. Bounded by corpus size (~700 docs).
- **Consistency:** Build once, never invalidated. The BM25 index is static (loaded at startup from disk artifacts), so cached vectors are always consistent.
- **Why cache:** Building a sparse TF vector requires scanning the full `tf_index` (tens of thousands of terms) for each document. Building on every MMR iteration would be O(candidates × terms). Caching makes it O(terms) total per request.

### `RAGRepository._ollama_available` / `_available_models` — `rag_repository.py:54-56`

```python
self._ollama_available: Optional[bool] = None
self._available_models: list[str] = []
self._connection_status: str = "Not checked yet."
```

- **Initialized:** `None` — checked lazily on first LLM request
- **Mutation:** First `_ensure_ollama_checked()` call sets these and never re-checks
- **Why cache:** Ollama availability doesn't change during a process lifetime. Checking `client.list()` on every request would add ~200ms to every LLM call.
- **Tradeoff:** If Ollama is started after the first LLM request, it won't be discovered until the process restarts. This is acceptable for a development tool.

### `RAGRepository._article_lookup` / `_clause_structure` — `rag_repository.py:58-59`

```python
self._article_lookup: dict[str, dict] = {}
self._clause_structure: dict[str, dict] = {}
```

- **Built:** In `RAGRepository.__init__()` via `_build_article_lookup()`
- **Content:** Maps `article_no` → full article text (merged from clauses), and clause structure for context truncation
- **Mutability:** Read-only after construction
- **Why cache:** Building the lookup requires iterating all ~700 documents. Doing this per-request would be wasteful.

---

## Per-Request State

### `request.user` — Flask request context

```python
request.user = payload  # set by @token_required decorator
```

- **What:** Decoded JWT payload containing `user_id`, `token_version`, `exp`
- **Lifetime:** Single HTTP request. Flask tears down the request context after the response is sent.
- **Accessed by:** Controllers (`ask()`, `list_messages()`, etc.) to identify the authenticated user.
- **Thread safety:** Flask's request context is thread-local — each thread sees its own `request`.

---

## Frontend State

### React Component State

| Component | State Variable | Type | Purpose |
|-----------|---------------|------|---------|
| `mainsearchbar.jsx` | `query` | string | Controlled input value |
| `mainsearchbar.jsx` | `result` | object \| null | Full API response |
| `mainsearchbar.jsx` | `loading` | boolean | Show spinner during request |
| `mainsearchbar.jsx` | `error` | string \| null | Error display |
| `mainsearchbar.jsx` | `streaming` | boolean | Whether SSE is active |
| `mainsearchbar.jsx` | `cancelled` | boolean | User cancelled streaming |
| `mainsearchbar.jsx` | `streamingAnswer` | string | Accumulated tokens during stream |
| `ArticleCard.jsx` | `expanded` | boolean | Card accordion toggle |
| `LoginPage.jsx` | `email`, `password` | string | Form state |
| `HistoryPage.jsx` | `messages` | array | Paginated message list |
| `HistoryPage.jsx` | `page` | number | Current pagination page |
| `MessageDetailPage.jsx` | `message` | object \| null | Loaded message with articles |

### React Refs

| Component | Ref | Purpose |
|-----------|-----|---------|
| `mainsearchbar.jsx` | `abortRef` (AbortController) | Cancels in-flight streaming request |
| `Dialog.jsx` | `dialogRef` | Focus trap for modal dialog |

### Auth Context

**File:** `frontend/src/context/AuthProvider.jsx`

| State | Storage | Purpose |
|-------|---------|---------|
| `token` | `localStorage` + React state | JWT for Authorization header |
| `user` | React state | User profile (fullname, email, id) |
| `loading` | React state | Initialization flag (checks localStorage on mount) |

**Persistence:** On login, `setToken()` writes to both `localStorage` and React state. On logout, both are cleared.

**Consistency:** The JWT is the source of truth. The `localStorage` value is read on app mount to restore session across page refreshes. If the JWT expires or is invalidated, the server returns 401 and the `api/client.js` interceptor clears `localStorage` and redirects to `/login`.

### URL State

| State | Mechanism | Purpose |
|-------|-----------|---------|
| Current route | `react-router-dom` (BrowserRouter) | Page navigation, history |
| `message_id` | URL param `/messages/:id` | Identify which message to load |

---

## State Consistency Summary

| Concern | Mechanism |
|---------|-----------|
| **Auth invalidation** | Token version comparison (DB is truth, JWT carries version snapshot) |
| **No dirty reads** | All DB writes precede response; persistence is fire-and-forget after response assembled |
| **Cache staleness** | `_ollama_available` never re-checks (intentional — Ollama is static per session) |
| **Thread safety (global)** | `_workflow`, `_spacy_nlp`, caches are read-only after init; no writes during request handling |
| **Thread safety (singleton)** | `Database.__new__` unsynchronized but safe — called once during startup |
| **Frontend session** | JWT in `localStorage` — single source of truth; cookie is fallback |
| **Race conditions** | None — every request is synchronous within its thread; no shared mutable state is written during requests |

---

## State Diagram: Lifecycle of a JWT

```
Registration
  ↓
User created → token_version = 0
  ↓
Login
  ↓
JWT issued with {user_id, token_version=0, exp=12h}
JWT → localStorage (frontend)
JWT → httpOnly cookie (backend)
  ↓
Every /ask request:
  JWT presented → jwt.decode() → payload.token_version=0
  User lookup → user.token_version=0 → match → allowed
  ↓
Logout
  ↓
User.token_version incremented → 1
  ↓
Next /ask request:
  JWT presented → payload.token_version=0
  User lookup → user.token_version=1 → mismatch → 401
  ↓
Frontend clears localStorage, redirects to /login
```

**Consistency property:** The logout is **immediately effective** for all existing JWTs because the version comparison hits the database on every request. There is no propagation delay, no token blacklist, no expiry wait.
