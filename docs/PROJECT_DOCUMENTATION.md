# Constitution Assistant — Complete System Documentation

**Project:** Explainable Constitutional IR and Assistance System
**Version:** 2.0.3 (code-based documentation refresh)
**Last Updated:** July 2026
**Authors:** Ronish Ghimire, Devraj Khatiwada, Nayan Nepal
**Domain:** Legal Information Retrieval — Constitution of Nepal (2072 / 2015)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Codebase Structure](#3-codebase-structure)
4. [API Documentation](#4-api-documentation)
5. [Database Documentation](#5-database-documentation)
6. [Business Logic](#6-business-logic)
7. [Feature Breakdown](#7-feature-breakdown)
8. [Setup & Environment](#8-setup--environment)
9. [Known Issues & Technical Debt](#9-known-issues--technical-debt)
10. [Design Decisions](#10-design-decisions)

---

## 1. Project Overview

### 1.1 What the System Does

**Constitution Assistant** is a Retrieval-Augmented Generation (RAG) system that answers natural-language questions about the **Constitution of Nepal (2072 / 2015)**. Users ask legal questions in plain English and receive:

1. **Ranked constitutional provisions** from a custom hybrid search engine (BM25 + term proximity + title boost + RRF/MMR reranking).
2. **Optionally, an LLM-generated answer** grounded strictly in the retrieved provisions (using Ollama + `qwen3:8b` by default).

### 1.2 Core Features

- **Hybrid Search Engine**: Custom BM25 (`k1=1.5`, `b=1.0`) + term proximity scoring + title boost for constitution-specific retrieval.
- **Synonym Expansion**: 44 synonym groups loaded from `data/synonyms.json` to improve recall across legal terminology variants.
- **Algorithmic Reranking**: RRF fusion (reciprocal rank fusion of BM25 + proximity + title-boost signals) + MMR diversity (maximal marginal relevance via BM25 cosine similarity) + rule-based boost (per-document, part-level, and level multipliers).
- **Article-Level Promotion**: Clause/sub-clause results are merged into full articles with matched-clause tracking and context truncation for LLM efficiency.
- **RAG (Retrieval-Augmented Generation)**: Ollama-powered LLM answer generation with strict grounding and 3-attempt retry logic.
- **Graceful Degradation**: If Ollama is unavailable → HTTP 503; if model is missing → retrieval-only with informative status.
- **User Authentication**: JWT-based registration/login/logout with bcrypt password hashing and token version invalidation.
- **Message Persistence**: Queries, LLM answers, and referenced articles are saved to MongoDB per user via `_persist_message()`.
- **Chat History API**: Full CRUD for user Q&A history with pagination and ownership enforcement.
- **Streaming Responses**: SSE-based streaming endpoint (`/ask-stream`) for real-time token delivery.
- **Offline Ingestion Pipeline**: Flatten nested constitution JSON → build term frequency / positional / document-stats indexes.

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React 19 + Vite 8)                 │
│                                                                  │
│  AuthProvider → localStorage JWT → Bearer header                │
│  useAskStream → SSE via ReadableStream.getReader()              │
│                                                                  │
│  Pages: Home, Login, Register, History, MessageDetail,          │
│         About, HowItWorks, NotFound                             │
│  UI: Navbar, MainSearchBar, Resultdisplay, ArticleCard,         │
│      Suggestion, ConfidenceBadge, ProtectedRoute                │
│  Primitives: Button, Input, Toggle, Card, Alert, Badge,        │
│              Spinner, Pagination, Dialog                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ POST /api/v1/ask (JWT Bearer auth)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (Flask / Python 3.13)                  │
│                                                                  │
│  ┌──────────┐  ┌────────────┐  ┌────────────────────────────┐  │
│  │  Routes   │  │Controllers │  │      Services               │  │
│  │(Blueprints)│  │(validation)│  │  QAService (orchestration)│  │
│  └──────────┘  └────────────┘  └──────────┬─────────────────┘  │
│                                            │                    │
│              ┌─────────────────────────────┼──────────────┐    │
│              │       RAGWorkflow           │              │    │
│              │  ┌───────────────────────┐  │              │    │
│              │  │   RAGRepository        │  │              │    │
│              │  │  (retrieval delegation │  │              │    │
│              │  │   + article promotion  │  │              │    │
│              │  │   + Ollama client)     │  │              │    │
│              │  └──────────┬────────────┘  │              │    │
│              │             │               │              │    │
│              │  ┌──────────▼────────────┐  │              │    │
│              │  │  RetrievalWorkflow     │  │              │    │
│              │  │  (search + rerank)     │  │              │    │
│              │  └─────┬──────────┬──────┘  │              │    │
│              │        │          │         │              │    │
│              │  ┌─────▼──┐  ┌───▼──────┐  │              │    │
│              │  │Search  │  │ Reranker  │  │              │    │
│              │  │Engine  │  │(RRF+MMR  │  │              │    │
│              │  │BM25+prx│  │ +boost)  │  │              │    │
│              │  └────────┘  └──────────┘  │              │    │
│              │                            │              │    │
│              │  ┌──────────────────────┐  │              │    │
│              │  │ Ollama LLM           │  │              │    │
│              │  │ (qwen3:8b default) │  │              │    │
│              │  └──────────────────────┘  │              │    │
│              └────────────────────────────┘              │    │
│                                                                  │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────────┐  │
│  │  Config       │  │  Models ODM    │  │  Preprocessing      │  │
│  │ (MongoDB      │  │(User/Message/  │  │  (flatten + build   │  │
│  │  singleton)   │  │  Article)      │  │   indexes + lemma)  │  │
│  └──────────────┘  └────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌───────────────────────────────┐
              │       MongoDB 8                │
              │  Database: ECIRAS              │
              │  Collections: users            │
              │                messages        │
              │                referenced_articles │
              └───────────────────────────────┘
```

### 2.2 Request Flow (Online Q&A)

1. User submits query via React frontend (JWT stored in `localStorage`, sent as `Authorization: Bearer` header).
2. Flask API validates: JSON content-type, parseable JSON, `query` is a non-empty string ≤ 500 chars, valid JWT.
3. `QAService.answer_query()` delegates to `RAGWorkflow.ask()`.
4. `RAGWorkflow` → `RAGRepository.retrieve()` → `RetrievalWorkflow.retrieve()`:
   - **Phase 1 (SearchEngine):** Tokenize with two processors, optionally expand synonyms, generate candidate set from BM25 tf_index, score each: `BM25(k1=1.5, b=1.0) + title_boost(5.0 × title matches) + proximity(1.0 × avg pair score)`, return top 30.
   - **Phase 2 (Reranker):** RRF fusion (k=60), MMR diversity (λ=0.5), rule-based boost (part/level multipliers), return top 8.
5. Results promoted to article level via `RAGRepository.promote_to_articles()` (clause/sub-clause docs merged into articles, deduplicated, matched clauses tracked).
6. If `use_llm=true` and Ollama is reachable and model is available:
   - Context truncated to matched clauses only
   - Format context → build system + user prompts with strict grounding
   - Call Ollama with 3-attempt retry (4096 context window, `keep_alive=30m`)
   - Return answer + citations
7. Response persisted: `_persist_message()` saves each article (via `ArticleService`, upsert by `doc_id`) and the query/answer pair (via `MessageService`).
8. Response returned as JSON (or SSE stream).

### 2.3 Offline Ingestion Flow

1. `flatten_constitution.py` reads nested JSON (`data/nepal_constitution_new.json`) → ~700 flat documents with enriched text, normalized citations, tokenized titles/bodies, boost values.
2. `IngestionWorkflow.build_indexes()` → `IndexBuilder` builds three indexes:
   - `tf_index.json` (term → {doc_id: tf}) using BM25 processor
   - `pos_index.json` (term → {doc_id: [positions]}) using proximity processor
   - `doc_stats.json` (doc_lengths + avgdl)


### 2.4 Tech Stack

| Layer          | Technology                          | Details                              |
|----------------|-------------------------------------|--------------------------------------|
| Backend        | Python 3.13 + Flask 3.x             | Flask with CORS, Blueprints          |
| Frontend       | React 19 + Vite 8                   | Tailwind CSS v4, JSX                 |
| Database       | MongoDB 8 (mongoengine ODM)         | 3 collections in `ECIRAS`            |
| IR Engine      | Custom Python                       | BM25 + term proximity + title boost + RRF/MMR reranking |
| NLP            | spaCy (`en_core_web_sm`)            | Lemmatization, tokenization          |
| LLM            | Ollama (local)                      | Default: `qwen3:8b`                |
| Auth           | JWT (HS256, 12h expiry)             | Bearer header + httpOnly cookie fallback, token versioning |

---

## 3. Codebase Structure

### 3.1 Root Directory

```
Constitution_assistant/
├── backend/                 # Flask API + retrieval engine + preprocessing
├── frontend/                # React 19 SPA
├── docs/                    # Documentation
│   ├── PROJECT_DOCUMENTATION.md   # This file
│   ├── api_docs.md                # API reference
│   ├── design.md                  # Design document
│   ├── algorithm_details.md       # Retrieval algorithm pseudo-code
│   └── mermaid/                   # Mermaid diagram sources + rendered outputs
├── references/              # Academic papers (PDFs)
├── postman/                 # Postman collections for API testing
├── temp/                    # Temporary notes
├── Makefile                 # Quick-start commands
├── AGENTS.md                # AI agent instructions
├── .gitignore
└── .prettierrc
```

### 3.2 Backend Structure

```
backend/
├── app.py                          # Flask factory, main()
├── requirements.txt                # UTF-16 encoded dependencies
├── .env.sample                     # Environment variable template
├── README.md                       # Backend-specific docs
├── Makefile                        # Build/run commands
│
├── routes/
│   ├── api_routes.py               # GET /api/v1, /health, /messages; POST /ask, /ask-stream; DELETE /messages
│   └── auth_routes.py              # /api/v1/auth/register, /login, /logout, /me
│
├── controllers/
│   ├── api_controller.py           # home(), health(), ask(), ask_stream(), message CRUD, _persist_message()
│   ├── auth_controller.py          # register(), login(), logout(), get_current_user()
│   └── decorators.py               # @token_required JWT decorator (Bear header + cookie fallback, token_version check)
│
├── services/
│   ├── qa_service.py               # Lazy singleton RAGWorkflow, answer_query(), answer_query_streaming()
│   ├── user_service.py             # CRUD + authenticate (JWT generation)
│   ├── message_service.py          # CRUD + pagination + search
│   └── article_service.py          # CRUD (upsert by doc_id)
│
├── models/
│   ├── user_model.py               # User (fullname, email, password_hash, role, token_version)
│   ├── message_model.py            # Message (query, answer, user ref, article refs)
│   └── referenced_article_model.py # ReferencedArticle (title, citation, doc_id, scores, metadata, terms)
│
├── config/
│   └── db_connect.py               # Database singleton (maxPoolSize=10, minPoolSize=2, 5s timeout)
│
├── src/
│   ├── core/                       # Information retrieval engine (no Flask deps)
│   │   ├── __init__.py             # Exports: Document, TextProcessor, BM25Scorer, ProximityScorer, SearchEngine
│   │   ├── document.py             # Document dataclass (all fields + boost)
│   │   ├── text_processor.py       # TextProcessor (normalize, lemmatize, stopwords, contractions)
│   │   ├── index_builder.py        # IndexBuilder (tf, positional, doc stats)
│   │   ├── bm25_scorer.py          # BM25Scorer (k1=1.5, b=1.0)
│   │   ├── proximity.py            # ProximityScorer (ordered term pairs, pair heuristic)
│   │   ├── search_engine.py        # SearchEngine (candidate generation, hybrid scoring)
│   │   ├── reranker.py             # Reranker (RRF fusion + MMR diversity + rule-based boost)
│   │   ├── engine_factory.py       # EngineFactory (loads artifacts from disk, optional synonym expander)
│   │   ├── query_expander.py       # QueryExpander (44 synonym groups from data/synonyms.json)
│   │
│   ├── llm/
│   │   ├── ollama_llm.py           # createOllamaClient() factory
│   │   ├── rag_repository.py       # RAGRepository (retrieval, article promotion, context truncation, Ollama client)
│   │   ├── rag_formatter.py        # RAGFormatter (context formatting, system/user prompt building)
│   │   └── rag_workflow.py         # RAGWorkflow (orchestrator: repo + formatter)
│   │
│   ├── constants/
│   │   ├── contraction_map.py      # 57 English contractions → expansions
│   │   └── stopwords.py            # ~120 English stopwords
│   │
│   └── workflows/
│       ├── ingestion_workflow.py   # IngestionWorkflow (load → build → save indexes)
│       └── retrieval_workflow.py   # RetrievalWorkflow (SearchEngine.search(recall_k=50) → Reranker.rerank(top_k=8))
│
├── preprocessing_scripts/
│   ├── run_ingestion.py            # Full pipeline orchestration
│   ├── flatten_constitution.py     # Nested JSON → flat document list
│   ├── build_index.py              # Flat docs → indexes
│
├── data/
│   ├── nepal_constitution_new.json # Nested format input (parts → articles → clauses)
│   ├── nepal_constitution.json     # Alternative flat list format input
│   ├── synonyms.json               # 44 synonym groups for query expansion
│   └── output/                     # Generated artifacts (gitignored)
│       ├── flattened_nepal_constitution.json
│       ├── tf_index.json
│       ├── pos_index.json
│       └── doc_stats.json
│
├── json_builder_tools/             # Browser-based JSON editing tools
│   ├── constitution_schema.md
│   ├── constitution_preview.html
│   ├── json_builder_v2.html
│   └── json_builder_v3.html
│
└── temp/                           # Temp files (gitignored)
    └── tests/                      # Pytest test suite
```

### 3.3 Frontend Structure

```
frontend/
├── index.html                      # SPA entry: <div id="root">
├── package.json                    # React 19, Vite 8, Tailwind v4, react-router-dom, react-markdown
├── vite.config.js                  # Vite config: @vitejs/plugin-react + @tailwindcss/vite
├── eslint.config.js                # Flat config: JSX, React hooks, React Refresh
├── README.md                       # Stale Vite template (not authoritative)
│
└── src/
    ├── main.jsx                    # Mounts <App /> into #root
    ├── index.css                   # Tailwind v4 import + @theme custom colors
    ├── App.jsx                     # BrowserRouter with routes, AuthProvider wrapper
    │
    ├── api/
    │   └── client.js               # Fetch wrapper (Bearer token, 100s timeout)
    │
    ├── context/
    │   ├── authContext.js           # createContext(null)
    │   ├── useAuth.js              # useContext + null guard
    │   └── AuthProvider.jsx        # login/register/logout, localStorage token management
    │
    ├── hooks/
    │   └── useAskStream.js         # SSE streaming via ReadableStream.getReader()
    │
    ├── components/
    │   ├── Navbar.jsx              # Sticky top nav (responsive hamburger)
    │   ├── mainsearchbar.jsx       # Search input + AI toggle + Cancel + Suggestion pills
    │   ├── Suggestion.jsx          # 6 preset query buttons
    │   ├── Resultdisplay.jsx       # Two-column: markdown answer + article cards
    │   ├── ArticleCard.jsx         # Expandable card with scoring breakdown + term highlighting
    │   ├── ConfidenceBadge.jsx     # Colored score badge (green/amber/red)
    │   └── ProtectedRoute.jsx      # Auth gate, redirects to /login
    │
    │   └── ui/                     # UI primitives
    │       ├── Button.jsx          # Variants (primary/secondary/danger/ghost), sizes (sm/md/lg)
    │       ├── Input.jsx           # Floating label, error state, helper text
    │       ├── Toggle.jsx          # Switch toggle (role="switch")
    │       ├── Card.jsx            # Container with optional header/footer
    │       ├── Alert.jsx           # Notification banner (error/success/warning/info)
    │       ├── Badge.jsx           # Inline colored badge
    │       ├── Spinner.jsx         # Animated loading spinner (sm/md/lg)
    │       ├── Pagination.jsx      # Previous/Next navigation
    │       └── Dialog.jsx          # Modal confirmation (overlay, Esc, focus trap)
    │
    ├── utils/
    │   └── highlight.jsx           # HighlightText — wraps matched terms in <mark>
    │
    ├── pages/
    │   ├── HomePage.jsx            # Main search interface
    │   ├── LoginPage.jsx           # Email/password form
    │   ├── RegisterPage.jsx        # Full name/email/password form
    │   ├── HistoryPage.jsx         # Paginated chat history with delete
    │   ├── MessageDetailPage.jsx   # Single message detail with Resultdisplay
    │   ├── AboutPage.jsx           # Static about
    │   ├── HowItWorksPage.jsx      # 4-step process
    │   └── NotFoundPage.jsx        # 404
    │
    └── data/
        ├── constitution_flattened.json     # Local copy of flattened constitution
        └── constitution_flattened_old.json # Older format
```

### 3.4 Entry Points

| Entry Point | Command | Purpose |
|-------------|---------|---------|
| Flask Server | `python backend/app.py` | Starts API server on `http://127.0.0.1:5000` |
| Frontend Dev | `cd frontend && npm run dev` | Vite dev server on `http://localhost:5173` |
| Manual Ingestion | `python -m preprocessing_scripts.run_ingestion` | Full pipeline (flatten → index → lemma) |
| Build Indexes | `python -m preprocessing_scripts.build_index` | Indexes only from existing flattened JSON |
| RAG CLI Demo | `python -m src.llm.rag_workflow` | Standalone demo with 3 preset questions |

---

## 4. API Documentation

See [api_docs.md](api_docs.md) for the complete API reference with request/response examples.

### 4.1 Quick Reference

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/v1` | No | API landing + endpoint list |
| GET | `/api/v1/health` | No | Liveness check |
| POST | `/api/v1/ask` | Yes | Q&A (`query`, `use_llm`, saves to MongoDB) |
| POST | `/api/v1/ask-stream` | Yes | Streaming Q&A via SSE |
| GET | `/api/v1/messages` | Yes | Paginated chat history (`limit`, `skip`) |
| GET | `/api/v1/messages/<id>` | Yes | Single message + populated articles |
| DELETE | `/api/v1/messages/<id>` | Yes | Delete message (owner only) |
| DELETE | `/api/v1/messages` | Yes | Delete all user messages |
| POST | `/api/v1/auth/register` | No | User registration |
| POST | `/api/v1/auth/login` | No | Login (JWT in body + httpOnly cookie) |
| POST | `/api/v1/auth/logout` | Yes | Invalidates token (increments `token_version`) |
| GET | `/api/v1/auth/me` | Yes | Current user profile |

### 4.2 Authentication

- JWT (HS256) with 12-hour expiry
- **Frontend** stores token in `localStorage`, sends via `Authorization: Bearer` header
- **Backend** also sets `token` cookie (httpOnly, SameSite=Strict, Secure in production) as fallback
- The `@token_required` decorator checks `token_version` from the JWT payload against the user document in MongoDB — logout increments `token_version`, invalidating all existing JWTs

### 4.3 Validation

- `/ask` and `/ask-stream`: Content-Type must be `application/json`, body must be valid JSON, `query` required (string, max 500 chars)
- `/register`: `fullname` required (3-50 chars), `email` must match regex, `password` min 6 chars, `role` must be `"user"` or `"admin"`
- Pagination defaults: `limit=20`, `skip=0`

### 4.4 Error Responses

All errors follow: `{ "error": "description" }`

| Status | Meaning |
|--------|---------|
| 400 | Bad request (validation) |
| 401 | Unauthorized (missing/expired/invalid token, `token_version` mismatch) |
| 403 | Forbidden (resource ownership) |
| 404 | Not found |
| 500 | Internal server error |
| 503 | Ollama service unavailable |

---

## 5. Database Documentation

### 5.1 Connection

**Database name:** `ECIRAS`
**Driver:** mongoengine ODM via `config/db_connect.py` (singleton, `maxPoolSize=10`, `minPoolSize=2`, 5s timeouts)
**Startup behavior:** Server fails fast if MongoDB is unreachable

### 5.2 Collection: `users`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `_id` | ObjectId | auto | Primary key |
| `fullname` | String | required, min_length=3, max_length=50 | Display name |
| `email` | String | required, unique | Login identifier |
| `password_hash` | String | required | bcrypt hash (60 chars) |
| `role` | Enum (`user`, `admin`) | default=`user` | Authorization level |
| `token_version` | Int | default=0 | Incremented on logout to invalidate JWTs |
| `created_at` | DateTime | auto-set on creation | |
| `updated_at` | DateTime | auto-updated on save | |

**Indexes:** `email` (unique), `(fullname, created_at)` (composite)
**Ordering:** `-created_at` (newest first)
**Methods:**
- `set_password(password)` — bcrypt `gensalt()` + `hashpw()`
- `check_password(password)` — bcrypt `checkpw()`
- `to_json()` — returns dict excluding `password_hash` and `role`

### 5.3 Collection: `messages`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `_id` | ObjectId | auto | Primary key |
| `query` | String | required | User question |
| `answer` | String | | LLM-generated answer (empty if retrieval-only) |
| `user` | Reference (User) | required, CASCADE on delete | Owner |
| `articles` | List\[Reference(ReferencedArticle)\] | default=\[], NULLIFY on delete | Referenced provisions |
| `created_at` | DateTime | auto-set | |
| `updated_at` | DateTime | auto-updated | |

**Indexes:** `query`, `user`, `(query, created_at)`
**Ordering:** `-created_at`

### 5.4 Collection: `referenced_articles`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `_id` | ObjectId | auto | Primary key |
| `title` | String | required | Article title (e.g., "Right relating to education") |
| `citation` | String | required | e.g., "Part 3, Article 31" |
| `doc_id` | String | required | Unique document ID from flattened corpus |
| `relevance_score` | Float | required, min_value=0.0 | Combined final score after reranking |
| `bm25_score` | Float | default=0.0 | Raw BM25 score |
| `proximity_score` | Float | default=0.0 | Raw proximity score |
| `title_match_count` | Int | default=0 | Number of query tokens matched in title |
| `article_no` | Int | | Corresponding article number |
| `clause_no` | String | | Clause label (e.g., "1", "2") |
| `subclause_id` | String | | Sub-clause identifier |
| `level` | String | | `"article"`, `"clause"`, or `"subclause"` |
| `part_no` | Int | | Corresponding part number |
| `text` | String | | Truncated text for LLM context |
| `full_text` | String | | Full provision text |
| `matched_terms` | List\[String\] | default=\[] | BM25-matched terms (lemmatized) |
| `exact_matched_terms` | List\[String\] | default=\[] | Exact-match terms (for frontend highlighting) |
| `created_at` | DateTime | auto-set | |
| `updated_at` | DateTime | auto-updated | |

**Indexes:** `title`, `citation`, `doc_id`, `(title, created_at)`
**Ordering:** `-created_at`

### 5.5 Entity Relationships

```
User (1) ─────── creates ──────→ Message (0..*)
Message (0..*) ── references ──→ ReferencedArticle (0..*)
```

- Deleting a User CASCADE-deletes their Messages (`reverse_delete_rule=2`)
- Deleting a ReferencedArticle NULLIFYs the reference from Messages (`reverse_delete_rule=3`)
- `_persist_message()` upserts articles by `doc_id` (updates existing, creates new)

---

## 6. Business Logic

### 6.1 Retrieval Pipeline (SearchEngine)

The core retrieval logic is in `src/core/search_engine.py`:

| Constant | Value | Description |
|----------|:-----:|-------------|
| `DEFAULT_PROXIMITY_WEIGHT` | 1.0 | Factor for proximity score vs. BM25 |
| `DEFAULT_TITLE_BOOST` | 5.0 | Bonus per matching query token in article title |
| `DEFAULT_MAX_WINDOW` | 30 | Maximum token distance for proximity pairs |
| `BM25_k1` | 1.5 | Term frequency saturation |
| `BM25_b` | 1.0 | Document length normalization |
| `recall_k` | 30 | Candidate set size from Phase 1 |
| `top_k` | 8 | Final results after reranking |

#### Algorithm: Retrieve(query, recall_k, top_k)

```
INPUT:  query (string), recall_k (int=30), top_k (int=8)
OUTPUT: List of scored document dicts

--- Phase 1: SearchEngine.search() ---

 1. bm25_tokens   ← TextProcessor.process(query, lemmatize=true,  remove_stopwords=true)
 2. base_tokens   ← copy(bm25_tokens)
 3. IF synonym_expander exists:
 4.     bm25_tokens ← synonym_expander.expand(bm25_tokens, raw_query=query)
 5. raw_tokens    ← TextProcessor.process(query, lemmatize=false, remove_stopwords=false)
 6. query_pairs   ← ProximityScorer.generate_query_pairs(raw_tokens)
 7. candidates    ← UNION of tf_index[token].keys() for each token in bm25_tokens
 8. FOR each doc in documents WHERE doc.doc_id IN candidates:
 9.     bm25       ← BM25Scorer.score(bm25_tokens, doc.doc_id)
10.     IF bm25 == 0: skip
11.     title_bonus ← |bm25_tokens ∩ title_tokens[doc.doc_id]| × 5.0
12.     prox       ← ProximityScorer.score(doc.doc_id, query_pairs, max_window=30, ordered=true)
13.     final      ← bm25 + title_bonus + 1.0 × prox
14.     scored.append((final, bm25, prox, title_matches, doc, matched_terms, exact_matched_terms))
15. Sort scored DESCENDING by final
16. RETURN top recall_k entries with full metadata

--- Phase 2: Reranker.rerank() ---

Stage 2a — RRF Fusion (k=60):
17. rank each result by bm25_score, proximity_score, title_match_count (separately)
18. rrf_score ← 1/(60+rank_bm25) + 1/(60+rank_prox) + 1/(60+rank_title)
19. Sort by rrf_score DESC

Stage 2b — MMR Diversity (λ=0.5):
20. selected ← [results[0]] (highest RRF)
21. WHILE candidates remain:
22.     FOR each candidate:
23.         mmr ← 0.5 × rrf_score - 0.5 × max(cosine_similarity(candidate, selected))
24.     Move highest-mmr candidate to selected

Stage 2c — Rule-Based Boost:
25. FOR each result:
26.     multiplier ← result.boost × part_rules[part_no] × level_rules[level]
27.     result.score ×= multiplier
28. Sort by score DESC
29. RETURN top top_k entries
```

### 6.2 BM25 Scoring

**Formula** (`src/core/bm25_scorer.py`):

$$
\text{score}(D, Q) = \sum_{t \in Q} \text{IDF}(t) \times
\frac{\text{tf}(t, D) \times (k_1 + 1)}
     {\text{tf}(t, D) + k_1 \times \left(1 - b + b \times \dfrac{|D|}{\text{avgdl}}\right)}
$$

$$
\text{IDF}(t) = \log\left(\frac{N - \text{df}(t) + 0.5}{\text{df}(t) + 0.5} + 1\right)
$$

| Parameter | Value | Notes |
|-----------|:-----:|-------|
| `k1` | 1.5 | Standard BM25 saturation |
| `b` | 1.0 | Full length normalization |
| `N` | varies | Total number of documents in corpus |

**Edge cases:** doc_len=0 → 0.0; df=0 → idf=0.0 via explicit guard; tf=0 → term skipped.

### 6.3 Proximity Scoring

**Pair Heuristic** (`src/core/proximity.py`):

| Query length | Pairs | Complexity |
|:------------:|-------|:----------:|
| ≤ 5 tokens | All unordered | O(n²/2) |
| > 5 tokens | Adjacent only | O(n−1) |

**Distance metric:** Minimum ordered distance (two-pointer sweep, term1 before term2)
**Score:** average over all pairs — quadratic inverse

$$
\text{score}_{\text{pair}}(a, b) = \frac{1}{(d(a, b) + 1)^2}
$$
**Window cap:** 30 tokens (pairs beyond are discarded)

### 6.4 Reranking

| Stage | Method | Details |
|:-----:|--------|---------|
| 2a | RRF Fusion | `k=60`, fuses BM25 rank + proximity rank + title-match rank |
| 2b | MMR Diversity | `λ=0.5`, cosine similarity on BM25 TF vectors (sparse) |
| 2c | Rule Boost | `boost` × part_rules[part_no] × level_rules[level] |

Default level multipliers:
- `part`: 1.0
- `article`: 0.98
- `clause`: 0.95
- `subclause`: 0.90

### 6.5 Article Promotion

After reranking, `RAGRepository.promote_to_articles()` converts clause/sub-clause results to full articles:

1. **Group** documents by `article_no`
2. **Pre-built lookup** from `_build_article_lookup()`:
   - Articles with their own text (lettered sub_clauses) → use directly
   - Articles stored as individual numbered clauses → concatenate all clause texts with `\n---\n`
3. **Deduplicate** by `article_no` — first occurrence (highest score) wins
4. **Track matched clauses** per article for context truncation
5. `build_truncated_text()` returns only matched clause texts for LLM context efficiency

### 6.6 Synonym Expansion

**Implementation:** `src/core/query_expander.py`

- Loads 44 synonym groups from `data/synonyms.json`
- Examples: "arrest/detention/custody", "right/entitlement/prerogative"
- Applied to BM25 tokens only (not proximity tokens)
- Multi-word phrases only included if present in the raw query string
- Expanded tokens increase recall by matching documents that use synonym variants

### 6.7 Text Processing

**Implementation:** `src/core/text_processor.py`

Pipeline: `normalize_text()` → optional `lemmatize_tokens()` → optional `_filter_stopwords()`

1. **Normalize:** lowercase → expand 57 contractions → keep only alphabetic + whitespace
2. **Lemmatize:** spaCy `en_core_web_sm` (falls back to `spacy.blank("en")` if model missing — tokenization works, lemmas are identity)
3. **Stopwords:** ~120 English stopwords

Two processor configurations:

| Processor | Lemmatization | Stopwords | Purpose |
|-----------|:-------------:|:---------:|---------|
| `bm25_processor` | ON | REMOVED | BM25 scoring and candidate generation |
| `proximity_processor` | OFF | KEPT | Proximity pair matching |

### 6.8 RAG Workflow

**LLM Integration** (`src/llm/rag_repository.py`):

- **Client:** `ollama.Client` constructed from `OLLAMA_HOST`/`OLLAMA_API_KEY` env vars
- **Default model:** `qwen3:8b` (override via `OLLAMA_MODEL`)
- **Connectivity check:** Cached per process lifetime, first request kicks it off
- **Retry:** 3 attempts, 0.5s delay, 4096 context window, `keep_alive=30m`
- **Prompt style:** Strict grounding — "Answer ONLY using the Context"; cite precisely; decline if not in constitution

**QAService Decision Matrix:**

| `use_llm` | Ollama State | HTTP | Response |
|:---------:|--------------|:----:|----------|
| `false` | — | 200 | `query` + `articles` |
| `true` | Connected, model loaded | 200 | `query` + `articles` + `response` + `ollama_status` (all ok) |
| `true` | Connected, model missing | 200 | `query` + `articles` + `ollama_status` (model_available=false) |
| `true` | Unreachable | 503 | `error`: "Ollama service is unavailable." |
| `true` | LLM fails after 3 retries | 200 | `query` + `articles` + `response` (error text) + `error` field |

### 6.9 JWT Authentication Flow

```
@token_required decorator (controllers/decorators.py):
1. Extract token from:
   - Authorization: Bearer <token> header (primary)
   - token cookie (fallback)
2. If no token: 401 "Token is missing!"
3. If JWT_SECRET not configured: 500 server error
4. Decode with jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
5. Look up user by user_id from payload, compare token_version
   - If payload.token_version != user.token_version: 401 "Token has been invalidated"
6. Attach payload to request.user
7. On ExpiredSignatureError: 401 "Token has expired!"
8. On InvalidTokenError: 401 "Invalid token!"
```

### 6.10 Database Persistence

`_persist_message()` in `api_controller.py` is called on every successful (`status=200`) Q&A request:

1. Iterates articles in the response
2. Calls `ArticleService.create_article()` — upserts by `doc_id` (updates existing doc, creates new)
3. Collects MongoDB ObjectIds
4. Calls `MessageService.create_message()` — saves query, answer, and article references

Persistence failures are **logged but never break the response** (fire-and-forget).

---

## 7. Feature Breakdown

### 7.1 Implemented Features

| Feature | Status | Location |
|---------|--------|----------|
| Hybrid Search Engine (BM25 + proximity + title boost) | ✅ Complete | `src/core/search_engine.py` |
| Offline Ingestion Pipeline (flatten → build indexes → lemma dict) | ✅ Complete | `preprocessing_scripts/` |
| Synonym Expansion (44 groups) | ✅ Complete | `src/core/query_expander.py` |
| Algorithmic Reranking (RRF + MMR + rule boost) | ✅ Complete | `src/core/reranker.py` |
| Article Promotion & Context Truncation | ✅ Complete | `src/llm/rag_repository.py` |
| Flask API Server (Blueprint-based, CORS, logging) | ✅ Complete | `app.py`, `routes/` |
| Main Q&A Endpoint with validation + graceful degradation | ✅ Complete | `controllers/api_controller.py` |
| SSE Streaming Endpoint | ✅ Complete | `POST /api/v1/ask-stream` |
| RAG with Ollama (3-attempt retry, 4096 ctx) | ✅ Complete | `src/llm/rag_repository.py` |
| Graceful LLM Degradation (3 outcomes) | ✅ Complete | `services/qa_service.py` |
| User Authentication (register/login/logout/me) | ✅ Complete | `controllers/auth_controller.py` |
| JWT Decorator with Bearer + cookie + token_version | ✅ Complete | `controllers/decorators.py` |
| Chat History API (CRUD, pagination, ownership) | ✅ Complete | `controllers/api_controller.py` |
| Message Persistence (query + answer + articles) | ✅ Complete | `_persist_message()` in `api_controller.py` |
| React Frontend SPA (search, toggle, streaming, history) | ✅ Complete | `frontend/src/` |
| Frontend UI Primitives (9 components) | ✅ Complete | `frontend/src/components/ui/` |
| Automated Tests | ✅ Partial | `backend/temp/tests/` (pytest) |

### 7.2 Known Gaps

| Gap | Cause |
|-----|-------|
| Admin API routes | `UserService.list_users()` / `delete_user()` exist but no admin blueprint exposed |
| CORS hardening | `CORS(app)` with no restrictions in `app.py:19` |
| Multi-model LLM fallback | No automatic fallback if `qwen3:8b` is missing |
| Retrieval-only dedicated endpoint | No separate `/api/v1/search` — uses `/ask?use_llm=false` |

---

## 8. Setup & Environment

### 8.1 Prerequisites

- Python 3.13+
- Node.js 22+
- MongoDB 8.0+ (local or remote)
- Ollama (optional, for LLM features)

### 8.2 Quick Start

**Backend:**
```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.sample .env
# Edit .env with your values
python -m preprocessing_scripts.run_ingestion  # First time only (builds indexes)
python app.py                   # Starts on http://127.0.0.1:5000
```

**Frontend:**
```powershell
cd frontend
npm install
npm run dev                     # Starts on http://localhost:5173
```

**Ollama (optional):**
```powershell
ollama serve
ollama pull qwen3:8b
```

### 8.3 Environment Variables

From `backend/.env`:

| Variable | Default | Required | Description |
|----------|---------|:--------:|-------------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | No | Ollama server URL |
| `OLLAMA_API_KEY` | (empty) | No | Bearer token for Ollama |
| `OLLAMA_MODEL` | `qwen3:8b` | No | Default LLM model |
| `MONGO_URI` | `mongodb://localhost:27017` | No | MongoDB connection |
| `MONGO_DB_NAME` | `ECIRAS` | No | Database name |
| `JWT_SECRET` | (must set) | Yes | HS256 signing key |

### 8.4 Python Dependencies

From `backend/requirements.txt` (UTF-16 encoded):

| Package | Used In |
|---------|---------|
| `flask` | Web framework, routes, controllers |
| `flask-cors` | CORS headers |
| `mongoengine` | MongoDB ODM (models) |
| `pymongo` | MongoDB driver (used by mongoengine) |
| `spacy` | NLP lemmatization / tokenization |
| `en_core_web_sm` | spaCy English model |
| `ollama` | LLM client SDK |
| `bcrypt` | Password hashing |
| `PyJWT` | JWT encode/decode |
| `python-dotenv` | `.env` loading |

### 8.5 Frontend Dependencies

From `frontend/package.json`:

| Package | Purpose |
|---------|---------|
| `react` 19 | UI library |
| `react-dom` 19 | React DOM renderer |
| `react-router-dom` 7 | Client-side routing |
| `react-markdown` 10 | Markdown rendering for LLM answers |
| `remark-gfm` 4 | GFM tables/strikethrough for markdown |
| `tailwindcss` 4 | Utility-first CSS |
| `@tailwindcss/vite` | Tailwind Vite plugin |
| `@vitejs/plugin-react` | Vite React plugin |
| `vite` 8 | Build tool / dev server |
| `eslint` 9 | Linting |

*(`pptxgenjs` is listed but unused in the codebase)*

### 8.6 Useful Commands

```powershell
# Backend
python app.py                          # Start server
python -m preprocessing_scripts.run_ingestion  # Full pipeline (flatten → index → lemma)
python -m preprocessing_scripts.build_index     # Indexes only
python -m src.llm.rag_workflow         # CLI RAG demo
pytest backend/temp/tests/             # Run tests

# Frontend
npm run dev                            # Dev server with HMR
npm run build                          # Production build
npm run lint                           # ESLint check
npm run preview                        # Preview production build

# Both together (root Makefile)
make backend                           # Start backend
make frontend                          # Start frontend
make run                               # Start both in separate windows
```

---

## 9. Known Issues & Technical Debt

### 9.1 Code Cleanup

| Issue | Location | Note |
|-------|----------|------|
| Unused CSS | `frontend/src/App.css` | ~150 lines of stale Vite boilerplate |
| Unused dep | `frontend/package.json` | `pptxgenjs` listed but never imported |
| Misleading async | `message_service.py`, `article_service.py` | Methods use `async def` with sync mongoengine — functionally correct but misleading |
| UTF-16 reqs | `backend/requirements.txt` | UTF-16 encoded; tools that expect UTF-8 will choke |

### 9.2 Registered Scope Decisions

| Decision | Detail |
|----------|--------|
| Message persistence | Fully wired via `_persist_message()` in both `/ask` and `/ask-stream` |
| `/me` response | Returns `UserService.get_user()` dict directly (`success`/`data`/`message` at top level) |
| `/ask` authenticated | `@token_required` enforced on all Q&A endpoints |
| User `to_json()` | Excludes `password_hash` and `role` by design |

---

## 10. Design Decisions

### 10.1 BM25 `b = 1.0` (Full Length Normalization)

The code uses `b = 1.0` rather than the more common `b = 0.75`. This applies **full** document length normalization — longer documents are penalized proportionally. For a legal constitution where provisions are of widely varying length (titles vs. multi-clause articles), this ensures that short, dense provisions are not overshadowed by verbose articles.

### 10.2 Why RAG instead of pure LLM?

Legal question-answering demands factual grounding. A pure LLM can hallucinate plausible-sounding but incorrect citations. RAG forces the LLM to answer strictly from retrieved articles with explicit citations.

### 10.3 Why two text processors?

| Processor | Lemmatization | Stopwords | Rationale |
|-----------|:-------------:|:---------:|-----------|
| BM25 | ON | REMOVED | "rights" and "right" should match; stopwords add noise to IDF |
| Proximity | OFF | KEPT | "right to education" ≠ "education right"; stopwords carry positional information |

### 10.4 Why the proximity pair heuristic?

Short queries (≤5 tokens) benefit from full cross-term proximity. Longer queries (>5 tokens) use adjacent pairs only to avoid O(n²) blowup — distant term pairs contribute negligible signal.

### 10.5 Why eager initialization for QAService?

- The pipeline (SearchEngine → Reranker → RetrievalWorkflow → RAGRepository → RAGWorkflow) is assembled once at startup in `init_workflow()`
- Startup latency is ~1s (loads 4 JSON indexes + spaCy model)
- Every HTTP request gets predictable response times — no slow first request
- Simpler code: no locks, no module-level `None` checks, no singleton pattern

### 10.6 Why token version invalidation?

On logout, `User.token_version` is incremented. Every subsequent request checks the JWT's `token_version` against the database — all existing JWTs become invalid immediately. This prevents replay attacks with stolen tokens and ensures logout is complete even if the cookie is not cleared.

### 10.7 Failure Mode Summary

| Failure | Behavior | User Sees |
|---------|----------|-----------|
| MongoDB offline | Fail-fast on server start | Connection error |
| Ollama not running, `use_llm=true` | Detection → HTTP 503 | `{"error": "Ollama service is unavailable."}` |
| Ollama running, model missing | Detection → HTTP 200 + articles | `ollama_status.model_available=false` |
| LLM call fails after 3 retries | Catches → HTTP 200 | Error text in `response` + `error` field |
| Invalid JSON | Validation → HTTP 400 | `{"error": "Invalid JSON payload."}` |
| Query > 500 chars | Validation → HTTP 400 | `{"error": "Query is too long..."}` |
| spaCy model missing | Falls back to blank `en` | Tokenization works; lemmas = identity |

---

*Documentation generated from codebase analysis. All details verified against the actual source code at `backend/` and `frontend/`.*
