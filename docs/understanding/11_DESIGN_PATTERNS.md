# Design Patterns

---

### 1. Factory (Static) — `EngineFactory.from_artifacts()`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/src/core/engine_factory.py:42` |
| **What** | `EngineFactory.from_artifacts(docs_path, index_dir, synonyms_path)` returns a fully-wired `SearchEngine` |
| **Why chosen** | Construction of a `SearchEngine` requires loading 4 JSON files from disk, creating 2 `TextProcessor` instances with different configurations, optionally loading a `QueryExpander`, and wiring 2 scorers. Exposing this in a constructor would force every caller to know about file formats and index structure. A factory encapsulates the entire assembly. |
| **Benefits** | Callers get a ready-to-use engine with one call. File-not-found errors are caught and reported with clear messages. Construction logic is centralized, not duplicated across tests, CLI scripts, and `init_workflow()`. |
| **Drawbacks** | Static factory cannot be mocked or subclassed. Tests that need a `SearchEngine` must either provide real files or bypass the factory entirely. |

---

### 2. Factory (Constructor Injection) — `RAGRepository.__init__()`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/src/llm/rag_repository.py:40` |
| **What** | `RAGRepository` constructor reads `OLLAMA_HOST`, `OLLAMA_API_KEY`, `OLLAMA_MODEL` from env vars and creates the `ollama.Client` internally |
| **Why chosen** | The Ollama client configuration is entirely environment-driven. Rather than forcing callers to pass host/api_key/model every time, the constructor reads them from the environment. Reduces boilerplate at every call site. |
| **Benefits** | Simple for callers — just pass the `RetrievalWorkflow`. Environment changes don't require code changes. |
| **Drawbacks** | Hidden dependency on environment variables makes testing harder (must set env vars or mock at the `ollama.Client` layer). The constructor has side effects (reading env vars) that can't be bypassed. |

---

### 3. Strategy — Scoring Algorithms

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/src/core/bm25_scorer.py` (BM25Scorer), `backend/src/core/proximity.py` (ProximityScorer), `backend/src/core/reranker.py` (Reranker — RRF, MMR, boost) |
| **What** | Each scoring algorithm is a self-contained class implementing a specific computation. They are composed by `SearchEngine` and `RetrievalWorkflow` interchangeably. |
| **Why chosen** | Each scoring signal (BM25, proximity, RRF fusion, MMR diversity, rule boost) is independently testable, replaceable, and tunable. Adding a new signal (e.g., embedding similarity) means writing a new scorer class without touching existing ones. |
| **Benefits** | High cohesion, low coupling. Each scorer has a single responsibility. BM25 can be swapped for BM25L or BM25+ by replacing one class. |
| **Drawbacks** | No common interface — each scorer has its own signature (`score(tokens, doc_id)` vs `score(doc_id, pairs)` vs `rerank(results)`). A formal interface would improve substitutability. |

---

### 4. Template Method — `SearchEngine.search()`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/src/core/search_engine.py:79` |
| **What** | `search()` defines the invariant pipeline skeleton: tokenize → expand → generate candidates → score each → sort → format. Subclasses or callers inject the scoring strategy. |
| **Why chosen** | Every search follows the same high-level sequence. The pipeline structure is fixed, but the scoring function could vary. The template method keeps the sequence in one place while allowing the scoring details to vary. |
| **Benefits** | The search algorithm is easy to follow — you read one method to understand the entire flow. New scoring signals slot in without changing the pipeline structure. |
| **Drawbacks** | Not a classic template method (no abstract subclass hooks). The scoring is determined by constructor-injected scorers rather than overridden methods. This is more **Strategy + Template Method** hybrid. |

---

### 5. Facade — `QAService`, `RAGWorkflow`, `RetrievalWorkflow`

| Aspect | Detail |
|--------|--------|
| **Where** | `services/qa_service.py:35`, `src/llm/rag_workflow.py:20`, `src/workflows/retrieval_workflow.py:5` |
| **What** | Each facade hides a complex subsystem behind a simple API: |
| | - `QAService` → hides EngineFactory, Reranker, RetrievalWorkflow, RAGRepository, RAGFormatter, ArticleService, MessageService |
| | - `RAGWorkflow` → hides RAGRepository (retrieval + Ollama), RAGFormatter |
| | - `RetrievalWorkflow` → hides SearchEngine + Reranker |
| **Why chosen** | The inner pipeline has many moving parts. Without facades, controllers would need to wire 8+ objects manually. Each facade defines a clear subsystem boundary and reduces cognitive load. |
| **Benefits** | Controllers are thin. The pipeline is layered: `ask()` → `QAService` → `RAGWorkflow` → `RAGRepository` → `RetrievalWorkflow` → `SearchEngine` + `Reranker`. Each layer hides the complexity below it. |
| **Drawbacks** | The facade layers add indirection. Debugging a query requires tracing through 5-6 delegation calls before reaching actual computation. The `QAService` facade is particularly thick — it both assembles the pipeline and handles persistence. |

---

### 6. Repository — `RAGRepository`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/src/llm/rag_repository.py:33` |
| **What** | `RAGRepository` abstracts two data sources: the retrieval pipeline (delegated to `RetrievalWorkflow`) and the LLM (Ollama client). Callers interact with `retrieve()` and `call_llm()` without knowing how either is implemented. |
| **Why chosen** | The Q&A workflow needs articles and an LLM answer. The repository pattern separates "what data is needed" from "where it comes from." If Ollama is replaced with an OpenAI API call, only `RAGRepository.call_llm()` changes. |
| **Benefits** | Clear data-access boundary. The repository owns connectivity caching, retry logic, and article lookup — none of which leak into the workflow. |
| **Drawbacks** | The name "Repository" is stretched — it doesn't mediate between domain and data mapping as in DDD. It mixes two different data sources (search + LLM) in one class. A stricter design would split into `RetrievalRepository` and `LLMRepository`. |

---

### 7. Active Record — MongoDB Models

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/models/user_model.py:12` (User), `message_model.py:7` (Message), `referenced_article_model.py:22` (ReferencedArticle) |
| **What** | Each model class combines data fields, persistence methods (`save()`), query logic (`objects.get()`), and business methods (`set_password()`, `check_password()`, `to_json()`) in a single class. |
| **Why chosen** | mongoengine is an Active Record ODM by design. For a project with simple CRUD and few model relationships, Active Record avoids the ceremony of a separate data-mapper layer. |
| **Benefits** | Rapid development — one class defines schema, queries, and behavior. No repository interfaces, no unit-of-work, no database abstraction layer. |
| **Drawbacks** | Violates Single Responsibility Principle. `User` handles persistence, password hashing, serialization, and validation. Testing business logic requires a running MongoDB (or extensive mocking). The models have no interface — swapping MongoDB for another database would require rewriting every model. |

---

### 8. Singleton — `Database`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/config/db_connect.py:7` |
| **What** | `Database._instance` class variable with `__new__` guard ensures exactly one instance per process |
| **Why chosen** | MongoDB connection pools must not be duplicated. The singleton guarantees `mongoengine.connect()` is called exactly once. |
| **Benefits** | Simple, well-understood, trivially correct for this use case. |
| **Drawbacks** | The `__new__` implementation is not thread-safe (two threads could pass the `None` check simultaneously). Safe in practice because `connect()` is called once during startup before any request threads exist. Harder to mock in tests compared to dependency injection. |

---

### 9. Lazy Initialization — spaCy Pipeline, Ollama Check, TF Vector Cache

| Aspect | Detail |
|--------|--------|
| **Where** | `text_processor.py:8` (`get_spacy_pipeline`), `rag_repository.py:291` (`_ensure_ollama_checked`), `reranker.py:29` (`_get_tf_vector`) |
| **What** | Expensive resources are initialized on first use, not at construction time. |
| **Why chosen** | The spaCy pipeline (~300ms, ~50MB) should not load if the IR engine is used only for offline ingestion. The Ollama check (~200ms) should not run if the user never enables LLM. TF vectors for MMR should not be built for documents that never appear in reranking. Lazy init defers cost until value is certain. |
| **Benefits** | Faster startup, lower memory when features are unused. The Ollama check is especially important — without lazy init, an unavailable Ollama would cause a visible startup warning or crash. |
| **Drawbacks** | First request pays the initialization cost (transparent to the user but visible in logs). Stateful lazy init (`_spacy_nlp`, `_ollama_available`) is module-level global, complicating test isolation. |

---

### 10. Decorator — `@token_required`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/controllers/decorators.py:28` |
| **What** | `@token_required` wraps route handlers with JWT validation logic |
| **Why chosen** | Authentication is a cross-cutting concern. Applying it as a decorator keeps route handlers clean of auth code and makes the auth requirement visible at the route definition. |
| **Benefits** | Eight protected routes share one auth implementation. The decorator extracts token from two sources (header + cookie), decodes JWT, checks token_version, and attaches `request.user`. Controllers just read `request.user.get("user_id")`. |
| **Drawbacks** | The decorator hits MongoDB on every request (`_get_user` for token_version check). For high-traffic endpoints, this adds latency. A token-blacklist cache could avoid the DB hit but introduces complexity. |

---

### 11. DTO (Data Transfer Object) — `Document`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/src/core/document.py:4` |
| **What** | `Document` is a `@dataclass` with 14 fields and no behavior. It carries data between the ingestion pipeline, the search engine, and the reranker. |
| **Why chosen** | A typed data object is safer than passing raw dicts. The dataclass gives field validation, IDE autocompletion, and explicit field names. |
| **Benefits** | Type safety without boilerplate. The dataclass is trivially constructable from JSON (`Document(**item)`). |
| **Drawbacks** | Not used everywhere — the SearchEngine returns `list[dict]`, not `list[Document]`. The dataclass is passed into the engine but not out. Inconsistent application of the pattern. |

---

### 12. Pipeline — `Reranker.rerank()`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/src/core/reranker.py:164` |
| **What** | `rerank()` runs three stages sequentially: RRF fusion → MMR diversity → rule boost. Each stage is a private method. |
| **Why chosen** | Three independent transformations applied in sequence. The pipeline makes the ordering explicit and allows adding/removing stages without changing the overall structure. |
| **Benefits** | The three stages are independently testable. Each stage has a clear input and output. Adding a fourth stage (e.g., semantic reranking) means writing one method and adding one call. |
| **Drawbacks** | Data is mutated in place (dicts are modified and returned) rather than creating immutable copies. This is fine within a single request but would be problematic if results were shared across threads. |

---

### 13. Builder — `RAGFormatter`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/src/llm/rag_formatter.py:1` |
| **What** | Three methods (`format_context()`, `build_system_prompt()`, `build_user_prompt()`) construct different parts of the LLM prompt independently. |
| **Why chosen** | The LLM prompt has three distinct parts (context, system instructions, user query). Builder separates construction of each part, making prompt changes isolated and testable. |
| **Benefits** | The system prompt can be updated without touching context formatting. The user prompt template can be changed without affecting system instructions. |
| **Drawbacks** | No director object — callers orchestrate the three builds manually. This is fine for two call sites (`ask()` and `ask_streaming()`) but would benefit from a director if more callers were added. |

---

### 14. Adapter (Implicit) — `RAGRepository` wrapping `ollama.Client`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/src/llm/rag_repository.py:52` |
| **What** | `RAGRepository` wraps `ollama.Client` and provides retry logic, connectivity caching, and a simpler interface (`call_llm(messages)` vs `client.chat(model, messages, ...)`). |
| **Why chosen** | The raw Ollama SDK exposes too many details (model name, context window, keep_alive). The adapter provides a domain-specific interface that callers (`RAGWorkflow`) can use without knowing about Ollama. |
| **Benefits** | Switching from Ollama to OpenAI requires changing only the adapter internals. The retry logic and connectivity caching are in one place. |
| **Drawbacks** | The adapter is tightly coupled to the Ollama response format (`response.message.content`). A different LLM provider would likely return a different response shape. |

---

### 15. Module-Level Singleton — `_workflow` in `qa_service.py`

| Aspect | Detail |
|--------|--------|
| **Where** | `backend/services/qa_service.py:20` |
| **What** | `_workflow: Optional[RAGWorkflow] = None` — the entire RAG pipeline is assembled once and stored as a module-level variable |
| **Why chosen** | Alternative to a class-based singleton. There must be exactly one pipeline per process. A module variable is simpler than a class Singleton with `__new__` and works the same way in practice. |
| **Benefits** | Dead simple — one global, one setter (`init_workflow()`), one getter (`_get_workflow()`). No locks, no class boilerplate. |
| **Drawbacks** | Module-level state is invisible to callers. Tests must explicitly reset the global between test cases. If `init_workflow()` raises, the module is in an undefined state. |

---

### 16. Composite — Frontend UI Primitives

| Aspect | Detail |
|--------|--------|
| **Where** | `frontend/src/components/ui/` (9 components) |
| **What** | Pages compose feature components (`MainSearchBar`, `Resultdisplay`), which compose UI primitives (`Button`, `Card`, `Spinner`, etc.). Components form a tree. |
| **Why chosen** | Natural in React — every component is a composable unit. The UI primitives provide a consistent baseline (all buttons look the same) while allowing feature components to vary layout. |
| **Benefits** | Visual consistency without CSS duplication. Primitives handle accessibility (aria attributes, focus management, keyboard events). |
| **Drawbacks** | The composition is React's default, not a deliberate pattern choice. The "composite" label describes what React already does, not a novel design decision. |

---

## Pattern Density Summary

| Pattern | Location | Strictness |
|---------|----------|:----------:|
| Factory (Static) | `EngineFactory.from_artifacts()` | ★★★★ |
| Factory (Constructor) | `RAGRepository.__init__()` (env vars) | ★★★ |
| Strategy | BM25Scorer, ProximityScorer, Reranker stages | ★★★★ |
| Template Method | `SearchEngine.search()` | ★★★ |
| Facade | QAService, RAGWorkflow, RetrievalWorkflow | ★★★★ |
| Repository | RAGRepository | ★★★ |
| Active Record | User, Message, ReferencedArticle (mongoengine) | ★★★★★ |
| Singleton | Database | ★★★★ |
| Lazy Initialization | spaCy, Ollama check, TF vector cache | ★★★★★ |
| Decorator | @token_required | ★★★★★ |
| DTO | Document dataclass | ★★★★ |
| Pipeline | Reranker (RRF → MMR → boost) | ★★★★ |
| Builder | RAGFormatter | ★★★ |
| Adapter | RAGRepository wrapping ollama.Client | ★★★ |
| Module Singleton | `_workflow` in qa_service.py | ★★★★ |
| Composite | Frontend UI primitives | ★★★ |

**Not used:** Event Bus, CQRS, Observer, Chain of Responsibility, Proxy, Flyweight, Visitor, Interpreter, Mediator, Memento, State.
