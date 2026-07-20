# Architecture & Module Dependencies

## Dependency Diagram

```
Routes (api_routes.py, auth_routes.py)
    │         │
    │         ├─── controllers/decorators.py ─── models/user_model.py
    │
    ▼
Controllers (api_controller.py, auth_controller.py)
    │
    ├─── services/qa_service.py
    │         │
    │         ├─── src/core/engine_factory.py  ← assembles IR engine
    │         ├─── src/core/reranker.py
    │         ├─── src/workflows/retrieval_workflow.py
    │         ├─── src/llm/rag_repository.py
    │         │         └─── src/workflows/retrieval_workflow.py  (again)
    │         ├─── src/llm/rag_workflow.py
    │         │         ├─── src/llm/rag_repository.py
    │         │         └─── src/llm/rag_formatter.py
    │         ├─── services/article_service.py ─── models/referenced_article_model.py
    │         └─── services/message_service.py ─── models/*
    │
    ├─── services/user_service.py ─── models/user_model.py
    ├─── services/message_service.py ─── models/*
    └─── services/article_service.py ─── models/referenced_article_model.py

src/workflows/retrieval_workflow.py
    │
    ├─── src/core/search_engine.py
    │         ├─── src/core/bm25_scorer.py       │
    │         ├─── src/core/proximity.py         │  (zero external deps)
    │         ├─── src/core/text_processor.py    │
    │         │         └─── src/constants/      │  (contractions, stopwords)
    │         ├─── src/core/query_expander.py    │
    │         └─── src/core/document.py          │
    │
    └─── src/core/reranker.py                  (zero external deps)

src/workflows/ingestion_workflow.py
    └─── src/core/index_builder.py ─── src/core/document.py

Frontend (React)
    App.jsx ─── pages ─── components ─── ui/ primitives
                │              └─── hooks/useAskStream
                │                        └─── api/client.js
                └─── context/AuthProvider ─── api/client.js
```

---

## Why Each Dependency Exists

| Edge                            | Reason                                                                                                    |
| ------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Routes → Controllers**        | Flask Blueprints wire URL paths to controller functions; thin pass-through layer                          |
| **Controllers → Services**      | Controllers handle HTTP concerns (parse request, return jsonify); Services hold business logic            |
| **Controllers → Models**        | `auth_controller` and `decorators` need direct model access for JWT user lookups and token_version checks |
| **Services → Workflows/LLM**    | `QAService.answer_query()` orchestrates the entire RAG pipeline — it's the application service            |
| **Services → Other Services**   | `QAService` calls `ArticleService` and `MessageService` for persistence                                   |
| **src/llm → src/workflows**     | `RAGRepository.retrieve()` delegates to `RetrievalWorkflow` for search+rerank                             |
| **src/workflows → src/core**    | `RetrievalWorkflow` composes SearchEngine + Reranker; `IngestionWorkflow` composes IndexBuilder           |
| **src/core/\* → src/constants** | `TextProcessor` needs contraction/stopword data for normalization                                         |
| **Frontend Pages → Components** | Page composition: pages import feature components like `MainSearchBar`, `Resultdisplay`                   |
| **Frontend Components → UI**    | Shared presentation primitives (Button, Card, Spinner) are consumed by feature components                 |

---

## Architectural Style

**Layered Architecture** with Clean Architecture influence in the backend.

```
┌──────────────────────────────────────────┐
│  Routes (HTTP entry)   — framework glue  │
├──────────────────────────────────────────┤
│  Controllers (HTTP)    — validation,     │
│                          request/response│
├──────────────────────────────────────────┤
│  Services (app logic)  — orchestration   │
├──────────────────────────────────────────┤
│  src/llm + workflows   — RAG pipeline    │
├──────────────────────────────────────────┤
│  src/core (IR engine)  — domain/models   │  ← pure Python, no framework
├──────────────────────────────────────────┤
│  Models (ODM)          — data boundary   │
└──────────────────────────────────────────┘
```

The `src/core/` package is the cleanest domain boundary — **zero imports** from Flask, mongoengine, or any framework. It only depends on Python stdlib and spaCy. This is the hallmark of Clean Architecture: the domain/inner layer is framework-agnostic.

---

## Tightly Coupled Modules

| Module                              | Reason                                                                                                                                                                                                               |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`services/qa_service.py`**        | Importing hub — depends on `engine_factory`, `reranker`, `retrieval_workflow`, `rag_repository`, `rag_workflow`, `rag_formatter`, `article_service`, `message_service`. Nearly every backend package converges here. |
| **`src/llm/rag_repository.py`**     | Spans two layers — imports from `src/workflows` and directly constructs `Ollama` clients                                                                                                                             |
| **`controllers/api_controller.py`** | Directly imports both `QAService` and `MessageService`                                                                                                                                                               |

## Loosely Coupled Modules

| Module                             | Reason                                                                   |
| ---------------------------------- | ------------------------------------------------------------------------ |
| **`src/core/bm25_scorer.py`**      | Pure math function — no imports beyond `math`. Swap-in replacement.      |
| **`src/core/reranker.py`**         | Same — pure algorithm with zero local imports.                           |
| **`src/core/proximity.py`**        | Self-contained pair scoring.                                             |
| **`src/core/query_expander.py`**   | Data → logic, no internal coupling.                                      |
| **`src/llm/rag_formatter.py`**     | Pure string builder — no dependencies on models, services, or workflows. |
| **`frontend/src/components/ui/*`** | Every UI primitive is a self-contained pure presentational component.    |

## Reusable Libraries

- **`src/core/`** — The entire IR engine (BM25, proximity, reranker, search engine, text processor) is a standalone library. It could be published as a Python package independently. It has no awareness of HTTP, databases, or LLMs.
- **`src/constants/`** — Contraction map and stopword list are reusable data artifacts.
- **`frontend/src/components/ui/`** — The 9 UI primitives (Button, Input, Card, etc.) are generic enough to extract into a shared component library.

## Architectural Boundaries

| Boundary                                      | Separates                                  | Nature                                                                            |
| --------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------- |
| **`controllers/` ↔ `services/`**              | HTTP concerns vs. app logic                | Clear — controllers never call `src/core/` directly                               |
| **`services/` ↔ `src/workflows/`/`src/llm/`** | App orchestration vs. domain pipeline      | Porous — `RAGRepository` is imported directly by `QAService`, bypassing workflows |
| **`src/workflows/` ↔ `src/core/`**            | Pipeline composition vs. atomic algorithms | Clean — workflows compose; cores compute                                          |
| **`src/core/` ↔ everything else**             | Domain IR logic vs. infrastructure         | **Strongest boundary** — core has no framework imports                            |
| **`models/` ↔ `services/`**                   | ODM schema vs. business logic              | Moderate — services import models for CRUD but models don't import services       |
| **Backend ↔ Frontend**                        | Server vs. client                          | Strict network boundary via REST API + JSON                                       |

---

## Notable Issues

1. **QAService is an import god-object** — it wires together 8+ modules. A dependency-injection container or factory pattern would reduce coupling.

2. **LLM layer leaks across boundaries** — `rag_repository.py` (in `src/llm/`) directly imports `RetrievalWorkflow` (in `src/workflows/`), meaning the LLM layer reaches down into the retrieval layer. A cleaner design would have `RAGWorkflow` own the composition.

3. **`async def` in services is misleading** — `MessageService` and `ArticleService` use `async def` but call sync mongoengine operations, making the async keyword a no-op.

4. **Frontend `api/client.js` is stateful** — module-level `token` variable mutated by `setToken()` creates implicit global state. This works in practice but is a subtle coupling.
