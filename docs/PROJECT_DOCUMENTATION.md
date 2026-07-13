# Constitution Assistant — Complete System Documentation

**Project:** Explainable Constitutional IR and Assistance System  
**Version:** 2.0.2 (documentation refresh)  
**Last Updated:** April 19, 2026  
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
9. [Issues & Technical Debt](#9-issues--technical-debt)
10. [Appendix: Mermaid Diagrams](#10-appendix-mermaid-diagrams)

---

## 1. Project Overview

### 1.1 What the System Does

**Constitution Assistant** is a Retrieval-Augmented Generation (RAG) system that answers natural-language questions about the **Constitution of Nepal (2072 / 2015)**. Users ask legal questions in plain English and receive:

1. **Ranked constitutional provisions** from a custom hybrid search engine (BM25 + term proximity + title boost).
2. **Optionally, an LLM-generated answer** grounded strictly in the retrieved provisions (using Ollama + Gemma3:1b).

### 1.2 Problem It Solves

The Constitution of Nepal is a lengthy legal document (over 300 articles across 35 parts). Finding relevant provisions for a specific legal question using keyword search or manual browsing is slow and error-prone. This system:

- Provides **instant, ranked retrieval** of constitution articles/clauses relevant to a user query.
- Uses **BM25 + term proximity + title boost** to rank provisions by both lexical relevance and phrase-level closeness.
- Optionally generates a **concise, citation-backed answer** using an LLM that is strictly grounded in retrieved articles — reducing hallucination in legal contexts.

### 1.3 Core Features

- **Hybrid Search Engine**: Custom BM25 scoring + term proximity scoring + title boost for constitution-specific retrieval.
- **RAG (Retrieval-Augmented Generation)**: Ollama-powered LLM answer generation with strict grounding.
- **Graceful Degradation**: If Ollama is unavailable, the system falls back to retrieval-only mode with informative status.
- **User Authentication**: JWT-based registration/login with bcrypt password hashing.
- **Message Persistence**: `MessageService` / `ArticleService` fully wired to `/ask` and `/ask-stream` — queries, LLM answers, and referenced articles are saved to MongoDB per user.
- **Chat History API**: CRUD endpoints for user Q&A history (`GET/DELETE /api/v1/messages`, `GET/DELETE /api/v1/messages/<id>`).
- **Algorithmic Reranking**: RRF fusion (reciprocal rank fusion of BM25 + proximity + title-boost signals) + MMR diversity (maximal marginal relevance via BM25 cosine similarity) + rule-based boost.
- **Offline Ingestion Pipeline**: Flatten nested constitution JSON → build term frequency / positional / document-stats indexes.
- **Frontend UI**: React 19 + Vite 8 single-page application with search, LLM toggle, and expandable result cards.

### 1.4 Document Conventions

- `backend/` refers to `c:\Users\Rons\OneDrive\Desktop\Constitution_assistant\backend`
- `frontend/` refers to `c:\Users\Rons\OneDrive\Desktop\Constitution_assistant\frontend`
- File paths are given relative to these roots unless otherwise noted.
- Marked **`[Assumption]`** where details were inferred rather than explicitly confirmed in code.

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   Frontend (React 19 + Vite 8)                │
│  Navbar │ SearchBar │ MainSearchBar │ ResultDisplay │ Suggs.  │
└──────────────────────────┬───────────────────────────────────┘
                           │ POST /api/v1/ask
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    Backend (Flask / Python 3.13)               │
│                                                               │
│  ┌──────────┐  ┌────────────┐  ┌──────────────────────────┐  │
│  │  Routes   │  │Controllers │  │      Services             │  │
│  │(Blueprints)│  │(validation)│  │  QAService (singleton)    │  │
│  └──────────┘  └────────────┘  └──────────┬───────────────┘  │
│                                            │                  │
│                    ┌───────────────────────┼──────────────┐   │
│                    │     RAGWorkflow       │              │   │
│                    │  ┌─────────────────┐  │              │   │
│                    │  │  RAGRepository   │  │              │   │
│                    │  │  (retrieval +    │  │              │   │
│                    │  │   Ollama client)  │  │              │   │
│                    │  └────────┬────────┘  │              │   │
│                    │           │           │              │   │
│                    │  ┌────────▼────────┐  │              │   │
│                    │  │RetrievalWorkflow │  │              │   │
│                    │  │  (search +       │  │              │   │
│                    │  │   rerank)        │  │              │   │
│                    │  └─────┬──────┬────┘  │              │   │
│                    │        │      │       │              │   │
│                    │  ┌─────▼──┐ ┌──▼──────┐             │   │
│                    │  │Search  │ │Reranker │             │   │
│                    │  │Engine  │ │(RRF+MMR │             │   │
│                    │  │BM25+prx│ │ +boost) │             │   │
│                    │  └────────┘ └─────────┘             │   │
│                    │                                      │   │
│                    │  ┌────────────────────────────────┐  │   │
│                    │  │ Ollama LLM (Gemma3:1b)         │  │   │
│                    │  └────────────────────────────────┘  │   │
│                    └──────────────────────────────────────┘   │
│                                                               │
│  ┌──────────┐  ┌────────────┐  ┌──────────────────────────┐  │
│  │  Config   │  │   Models   │  │      Preprocessing        │  │
│  │ (MongoDB) │  │(User/Message│  │  (flatten + index build)  │  │
│  │           │  │ /Article)   │  └──────────────────────────┘  │
│  └──────────┘  └────────────┘                                │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │      MongoDB 8             │
              │  users / messages /         │
              │  referenced_articles        │
              └───────────────────────────┘
```

### 2.2 Component Interaction Flow

**Online Q&A Flow:**
1. User submits query via React frontend or direct API call (requires JWT auth).
2. Flask API validates input (JSON, query length ≤ 500 chars, valid token).
3. `QAService` (lazy singleton) delegates to `RAGWorkflow`.
4. `RAGWorkflow.retrieve()` delegates to `RAGRepository` → `RetrievalWorkflow`:
   - **Phase 1 (High-recall search)**: `SearchEngine.search(query, top_k=30)` tokenizes query with two processors (BM25: lemmatized+no stopwords, Proximity: raw+stopwords kept), generates candidate set from BM25 term-frequency index, scores each candidate: `BM25 + title_boost(×5.0 per title match) + proximity_weight(×1.0 × avg pair score)`, returns top-30.
   - **Phase 2 (Reranking)**: `Reranker.rerank(results, top_k=8)` applies RRF fusion (combines BM25 + proximity + title-match ranks), MMR diversity (maximal marginal relevance via BM25 cosine), and rule-based boost (part/level multipliers). Returns top-8.
5. Results promoted to article level via `RAGRepository.promote_to_articles()` (clause/sub-clause docs merged into full articles, deduplicated).
6. If `use_llm=true` and Ollama is reachable, formats articles as context → builds strict prompt → calls Ollama with retry → returns answer + citations.
7. Response persisted: `_persist_message()` saves articles (via `ArticleService`) and query/answer (via `MessageService`) to MongoDB.
8. Response returned as JSON.

**Offline Ingestion Flow:**
1. `flatten_constitution.py` reads nested JSON (`data/nepal_constitution_new.json`) and produces flat document list.
2. `IngestionWorkflow` builds three JSON indexes: `tf_index.json`, `pos_index.json`, `doc_stats.json`.
3. `generate_safe_lemma_dict.py` builds a rule-based lemma dictionary for corpus-specific vocabulary.

### 2.3 Tech Stack

| Layer          | Technology                          | Details                              |
|----------------|-------------------------------------|--------------------------------------|
| Backend        | Python 3.13 + Flask 3.x             | Flask with CORS, Blueprints          |
| Frontend       | React 19 + Vite 8                   | Tailwind CSS v4, JSX                 |
| Database       | MongoDB 8 (mongoengine ODM)         | Users, messages, article refs        |
| IR Engine      | Custom Python                       | BM25 + term proximity + title boost + RRF/MMR reranking |
| NLP            | spaCy (`en_core_web_sm`)            | Lemmatization, tokenization          |
| LLM            | Ollama (local)                      | Default: `gemma3:1b`                 |
| Auth           | JWT (HS256, 12h expiry)             | httpOnly SameSite=Strict cookies + Bearer fallback |
| Build Tools    | Prettier, ESLint, Vite HMR          |                                      |

---

## 3. Codebase Structure

### 3.1 Root Directory

```
Constitution_assistant/
├── backend/                 # Flask API + retrieval engine + preprocessing
├── frontend/                # React 19 SPA
├── docs/                    # Documentation
│   ├── design.md            # Design document (canonical reference)
│   ├── algorithm_details.md # Pseudo-code for retrieval algorithm
│   ├── PROJECT_DOCUMENTATION.md  # This file
│   └── mermaid/             # Mermaid diagram sources and rendered outputs
├── references/              # Academic papers (PDFs)
├── postman/                 # Postman collections for API testing
├── Makefile                 # Quick-start commands for backend/frontend
├── .gitignore
├── .prettierrc
└── AGENTS.md                # AI agent instructions
```

### 3.2 Backend Structure (`backend/`)

```
backend/
├── app.py                          # Entry point: create_app(), --rebuild-data flag, main()
├── requirements.txt                # Python dependencies (UTF-16 encoded)
├── .env                            # Environment variables (gitignored)
├── .env.sample                     # Template for .env
├── README.md                       # Backend documentation
├── Makefile                        # Build commands
│
├── routes/                         # Flask Blueprints (URL routing)
│   ├── api_routes.py               #   GET /api/v1, /health, /messages; POST /ask, /ask-stream; DELETE /messages
│   └── auth_routes.py              #   /api/v1/auth/register, /login, /logout, /me
│
├── controllers/                    # Request validation and response formatting
│   ├── api_controller.py           #   home(), health(), ask(), ask_stream(), list/get/delete messages()
│   ├── auth_controller.py          #   register(), login(), logout(), get_current_user()
│   └── decorators.py               #   @token_required JWT decorator
│
├── services/                       # Business logic orchestration
│   ├── qa_service.py               #   QAService (singleton, double-checked locking)
│   ├── user_service.py             #   UserService (CRUD + authenticate)
│   ├── message_service.py          #   MessageService (CRUD + pagination + search)
│   └── article_service.py          #   ArticleService (CRUD)
│
├── models/                         # MongoDB ODM (mongoengine)
│   ├── user_model.py               #   User document
│   ├── message_model.py            #   Message document
│   └── referenced_article_model.py #   ReferencedArticle document
│
├── config/                         # Database configuration
│   └── db_connect.py               #   Database singleton (connect/disconnect)
│
├── src/
│   ├── core/                       # Information retrieval engine (no Flask deps)
│   │   ├── __init__.py             #   Public API exports
│   │   ├── document.py             #   Document dataclass
│   │   ├── text_processor.py       #   TextProcessor (normalize, lemmatize, stopwords)
│   │   ├── index_builder.py        #   IndexBuilder (tf, positional, doc stats)
│   │   ├── bm25_scorer.py          #   BM25Scorer (k1=1.5, b=0.75)
│   │   ├── proximity.py            #   ProximityScorer (ordered term pairs)
│   │   ├── search_engine.py        #   SearchEngine (candidate generation + scoring)
│   │   ├── reranker.py             #   Reranker (RRF fusion + MMR diversity + rule-based boost)
│   │   ├── engine_factory.py       #   EngineFactory (loads artifacts from disk)
│   │   └── app_bootstrap.py        #   rebuild_document_artifacts(), preload_spacy(), connect_database()
│   │
│   ├── llm/                        # RAG and LLM integration
│   │   ├── ollama_llm.py           #   createOllamaClient() factory
│   │   ├── rag_repository.py       #   RAGRepository (retrieval + article promotion + Ollama client)
│   │   ├── rag_formatter.py        #   RAGFormatter (context + prompt builder)
│   │   └── rag_workflow.py         #   RAGWorkflow (orchestrates repo + formatter)
│   │
│   ├── constants/                  # Shared constants
│   │   ├── contraction_map.py      #   57 English contractions → expansions
│   │   └── stopwords.py            #   ~120 English stopwords
│   │
│   └── workflows/                  # Workflow layer
│       ├── ingestion_workflow.py   #   IngestionWorkflow (load → build → save indexes)
│       └── retrieval_workflow.py   #   RetrievalWorkflow (high-recall search → rerank → top-k)
│
├── preprocessing_scripts/          # One-off pipeline scripts
│   ├── run_ingestion.py            #   Orchestrates all 3 steps
│   ├── flatten_constitution.py     #   Nested JSON → flat document list
│   ├── build_index.py              #   Load flattened docs → build indexes
│   └── generate_safe_lemma_dict.py #   Rule-based lemma dictionary
│
├── data/                           # Data files
│   ├── Constitution-of-Nepal_2072.pdf      # Source PDF
│   ├── nepal_constitution_new.json         # Nested format input
│   ├── nepal_constitution.json             # Alternative input format
│   └── output/                             # Generated artifacts (gitignored)
│       ├── flattened_nepal_constitution.json   # ~700+ flat documents
│       ├── tf_index.json                      # Term → {doc_id: tf}
│       ├── pos_index.json                     # Term → {doc_id: [positions]}
│       ├── doc_stats.json                     # doc_lengths + avgdl
│       └── lemma_dict_v3.json                 # Rule-based lemma map
│
├── json_builder_tools/             # Constitution JSON schema and tools
│   ├── constitution_schema.md      # Canonical JSON schema
│   ├── constitution_preview.html   # Preview tool
│   ├── json_builder_v2.html        # JSON builder (browser-based)
│   └── json_builder_v3.html        # Updated JSON builder
│
└── temp/                           # Temporary files (gitignored)
```

### 3.3 Frontend Structure (`frontend/`)

```
frontend/
├── index.html                      # SPA entry point
├── package.json                    # React 19, Vite 8, Tailwind v4
├── vite.config.js                  # Vite config (React + Tailwind plugins)
├── eslint.config.js                # ESLint flat config
├── README.md                       # Generated Vite template docs (stale)
│
├── public/
│   ├── favicon.svg                 # App favicon
│   └── icons.svg                   # Social media icons
│
└── src/
    ├── main.jsx                    # React root mount
    ├── index.css                   # Tailwind v4 import + base styles
    ├── App.jsx                     # Root component (layout assembly)
    ├── App.css                     # (Stale Vite boilerplate, not used)
    │
    ├── components/
    │   ├── Navbar.jsx              # Top navigation bar
    │   ├── SearchBar.jsx           # Hero section heading
    │   ├── mainsearchbar.jsx       # Main search input + LLM toggle + submission
    │   ├── Suggestion.jsx          # Quick-suggestion pills
    │   └── Resultdisplay.jsx       # Expandable result cards with related articles
    │
    └── data/
        ├── constitution_flattened.json      # Local copy of flattened constitution
        └── constitution_flattened_old.json  # Older format copy
```

### 3.4 Entry Points

| Entry Point | Path | Purpose |
|-------------|------|---------|
| Flask Server | `backend/app.py` | `$ python app.py` — starts the API server |
| Flask Server (rebuild) | `backend/app.py` | `$ python app.py --rebuild-data` — rebuilds indexes then starts server |
| Frontend Dev Server | `frontend/` | `$ npm run dev` — starts Vite dev server |
| Manual Ingestion | `backend/preprocessing_scripts/run_ingestion.py` | `$ python -m preprocessing_scripts.run_ingestion` |
| Build Indexes Only | `backend/preprocessing_scripts/build_index.py` | `$ python -m preprocessing_scripts.build_index` |
| RAG Demo | `backend/src/llm/rag_workflow.py` | `$ python -m src.llm.rag_workflow` (standalone demo) |

---

## 4. API Documentation

### 4.1 Base URL

`http://localhost:5000/api/v1`

### 4.2 Authentication

All auth endpoints return JWT tokens stored in **httpOnly, Secure, SameSite=Strict cookies** with 12-hour expiry. The `@token_required` decorator (`controllers/decorators.py`) checks for tokens in:
1. `Authorization: Bearer <token>` header (primary)
2. `token` cookie (fallback)

### 4.3 Endpoints

---

#### `GET /api/v1`

API landing page listing available endpoints.

**Response 200:**
```json
{
  "message": "Welcome to the API!",
  "endpoints": {
    "/api/v1/health": "Check the health of the API.",
    "/api/v1/ask": "Submit a query to get a response.",
    "/api/v1/auth/register": "Register a new user.",
    "/api/v1/auth/login": "Login with email and password.",
    "/api/v1/auth/logout": "Logout the current user.",
    "/api/v1/auth/me":"Get the current logged in user",
  },
  "version": "1.0.0"
}
```

---

#### `GET /api/v1/health`

Liveness check for the API server.

**Response 200:**
```json
{
  "status": "healthy"
}
```

#### Quick Test with curl

```bash
# Health check
curl http://localhost:5000/api/v1/health

# Retrieval-only query (no LLM)
curl -X POST http://localhost:5000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Right to education", "use_llm": false}'

# Full RAG query (requires Ollama running)
curl -X POST http://localhost:5000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the right to education?", "use_llm": true}'

# Register a user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"fullname": "Test User", "email": "test@example.com", "password": "pass123"}'

# Login (stores token as cookie)
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email": "test@example.com", "password": "pass123"}'

# Get current user (requires cookie from login)
curl http://localhost:5000/api/v1/auth/me -b cookies.txt
```

---

#### `POST /api/v1/ask`

Main Q&A endpoint. Accepts a natural language query and returns ranked constitutional provisions, optionally with an LLM-generated answer.

**Request Body:**
```json
{
  "query": "What is the right to education?",
  "use_llm": true
}
```

**Validation Rules:**
- Content-Type must be `application/json` → else **400**
- Request body must be valid JSON → else **400**
- `query` field is required, must be a string, max 500 characters → else **400**

**Behavior Matrix:**

| `use_llm` | Ollama Available | HTTP Status | Response Includes |
|:---------:|:----------------:|:-----------:|-------------------|
| `false`   | —                | 200         | `query` + `articles` |
| `true`    | Yes, model loaded | 200        | `query` + `articles` + `response` + `ollama_status` |
| `true`    | Yes, model missing | 200       | `query` + `articles` + `ollama_status` (no LLM answer) |
| `true`    | Unreachable      | 503         | `error`: "Ollama service is unavailable." |
| `true`    | LLM call fails after retries | 200 | `query` + `articles` + `response` (contains error text) + `error` field |

**Response 200 (Retrieval Only):**
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

**Response 200 (With LLM):**
```json
{
  "query": "What is the right to education?",
  "response": "Under the Constitution of Nepal, every citizen has the right to basic education... [Part 3, Article 31]...",
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

**Response 200 (Model Missing):**
```json
{
  "query": "What is the right to education?",
  "articles": [...],
  "ollama_status": {
    "connected": true,
    "model": "gemma3:1b",
    "model_available": false,
    "message": "Model 'gemma3:1b' is unavailable.",
    "available_models": ["llama3.2:3b", ...]
  }
}
```

**Response 400 (Validation Error):**
```json
{
  "error": "Query is too long. Maximum length is 500 characters."
}
```

**Response 500 (Server Error):**
```json
{
  "error": "An error occurred while processing the query."
}
```

**Response 503 (Ollama Unavailable):**
```json
{
  "error": "Ollama service is unavailable."
}
```

---

#### `POST /api/v1/auth/register`

Create a new user account.

**Request Body:**
```json
{
  "fullname": "John Doe",
  "email": "john@example.com",
  "password": "securepass123",
  "role": "user"
}
```

**Validation:**
- `fullname` and `email` are required
- `password` must be at least 6 characters
- `role` defaults to `"user"` (options: `"user"`, `"admin"`)
- Email must be unique → **400** if duplicate

**Response 201 (Success):**
```json
{
  "message": "User created successfully",
  "user": { "id": "...", "fullname": "John Doe", "email": "john@example.com", ... }
}
```

**Response 400 (Error):**
```json
{
  "error": "Validation Error: ...",
  "message": "Invalid user data provided."
}
```

---

#### `POST /api/v1/auth/login`

Authenticate and receive a JWT cookie.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepass123"
}
```

**Response 200 (Success):**
```json
{
  "message": "Login successful",
  "user": { "id": "...", "fullname": "John Doe", ... },
  "authenticated": true
}
```
Sets `token` cookie (httpOnly, Secure, SameSite=Strict, 12-hour expiry).

**Response 401 (Failure):**
```json
{
  "error": "Invalid credentials",
  "message": "Incorrect email or password."
}
```

---

#### `POST /api/v1/auth/logout`

Clear the authentication cookie.

**Auth:** Required (`@token_required`)

**Response 200:**
```json
{
  "message": "Logout successful."
}
```
Clears `token` cookie by setting `max_age=-1`.

---

#### `GET /api/v1/auth/me`

Get the currently authenticated user's information.

**Auth:** Required (`@token_required`)

**Response 200:**
```json
{
  "user": {
    "success": true,
    "data": { "id": "...", "fullname": "John Doe", ... },
    "message": "User retrieved successfully"
  }
}
```

**Response 404:**
```json
{
  "error": "User not found."
}
```

### 4.4 Endpoint Summary

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | /api/v1 | No | API landing + endpoints list |
| GET | /api/v1/health | No | Liveness check |
| POST | /api/v1/ask | Yes | Main Q&A (query + optional use_llm, persists to MongoDB) |
| POST | /api/v1/ask-stream | Yes | Streaming Q&A via SSE |
| GET | /api/v1/messages | Yes | Paginated chat history for current user |
| GET | /api/v1/messages/<id> | Yes | Single message with populated articles |
| DELETE | /api/v1/messages/<id> | Yes | Delete a single message (owner only) |
| DELETE | /api/v1/messages | Yes | Delete all messages for current user |
| POST | /api/v1/auth/register | No | User registration |
| POST | /api/v1/auth/login | No | Login, sets JWT cookie |
| POST | /api/v1/auth/logout | Yes | Clears JWT cookie |
| GET | /api/v1/auth/me | Yes | Current user info |---

## 5. Database Documentation

### 5.1 Database: `ECIRAS` (MongoDB via mongoengine)

Three collections managed by the ODM layer. Connection is handled by `config/db_connect.py` (singleton pattern, `maxPoolSize=10`, `minPoolSize=2`, 5s timeouts).

### 5.2 Collection: `users`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `_id` | ObjectId | auto | Primary key |
| `fullname` | String | required, min_length=3, max_length=50 | User's display name |
| `email` | String | required, unique | Login identifier |
| `password_hash` | String | required | bcrypt hash (60 chars) |
| `role` | Enum (`user`, `admin`) | default=`user` | Authorization level |
| `created_at` | DateTime | auto-set on creation | Timestamp |
| `updated_at` | DateTime | auto-updated on save | Timestamp |

**Indexes:** `email` (unique), `(fullname, created_at)` (composite)  
**Default ordering:** `-created_at` (newest first)  
**Methods:**
- `set_password(password)`: Hashes password with bcrypt `gensalt()`.
- `check_password(password)`: Verifies against stored hash.
- `to_json()`: Returns dict excluding `password_hash` and `role`.

### 5.3 Collection: `messages`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `_id` | ObjectId | auto | Primary key |
| `query` | String | required | User's natural language question |
| `answer` | String | optional | LLM-generated answer text |
| `user` | Reference (User) | required, CASCADE on delete | Owning user |
| `articles` | List[Reference(ReferencedArticle)] | default=[], NULLIFY on delete | Referenced constitutional articles |
| `created_at` | DateTime | auto-set | Timestamp |
| `updated_at` | DateTime | auto-updated | Timestamp |

**Indexes:** `query`, `user`, `(query, created_at)` (composite)  
**Default ordering:** `-created_at` (newest first)  
**`[Observation]`**: The `articles` field references `ReferencedArticle` documents. The `reverse_delete_rule=3` (NULLIFY) means deleting a referenced article removes it from the list but does not cascade to the message.

### 5.4 Collection: `referenced_articles`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `_id` | ObjectId | auto | Primary key |
| `title` | String | required | Article title (e.g., "Right relating to education") |
| `citation` | String | required | Citation string (e.g., "Part 3, Article 31") |
| `doc_id` | String | required | Document ID from the flattened constitution |
| `relevance_score` | Float | required, min_value=0.0 | BM25 + proximity combined score |
| `created_at` | DateTime | auto-set | Timestamp |
| `updated_at` | DateTime | auto-updated | Timestamp |

**Indexes:** `title`, `citation`, `doc_id`, `(title, created_at)` (composite)  
**Default ordering:** `-created_at`

### 5.5 Entity Relationships

```
User (1) ─────── creates ──────→ Message (0..*)
Message (0..*) ── references ──→ ReferencedArticle (0..*)
```

- A `User` can have many `Message` documents.
- Each `Message` belongs to exactly one `User` (CASCADE delete — deleting user removes their messages).
- A `Message` can reference zero or more `ReferencedArticle` documents (NULLIFY delete — deleting an article just removes the reference).
- `ReferencedArticle` documents are standalone and can be shared across multiple messages.

### 5.6 `[Assumption]`: Service-to-API Wiring

The `MessageService`, `UserService`, and `ArticleService` classes are fully implemented but **not connected** to the primary `/api/v1/ask` flow. The `QAService.answer_query()` method returns query results directly without persisting them to MongoDB. The auth endpoints (`/register`, `/login`, `/me`, `/logout`) do use `UserService`. The message/article persistence appears to be intended for future use (e.g., saving chat history).

---

## 6. Business Logic

### 6.1 Retrieval Pipeline (SearchEngine)

The core retrieval logic is in `src/core/search_engine.py` with tunable constants:

| Constant | Default | Description |
|----------|:-------:|-------------|
| `DEFAULT_PROXIMITY_WEIGHT` | 1.0 | Factor for proximity score vs. BM25 |
| `DEFAULT_TITLE_BOOST` | 5.0 | Bonus per matching query token in article title |
| `DEFAULT_MAX_WINDOW` | 30 | Maximum token distance for proximity pairs |
| `BM25_k1` | 1.5 | BM25 term frequency saturation |
| `BM25_b` | 0.75 | BM25 document length normalization |

#### Algorithm: Retrieve(query, top_k)

```
INPUT:  query (string), top_k (integer)
OUTPUT: List of (doc_id, score, metadata) sorted descending

1. bm25_tokens   ← TextProcessor.process(query, lemmatize=true,  remove_stopwords=true)
2. raw_tokens    ← TextProcessor.process(query, lemmatize=false, remove_stopwords=false)
3. candidates    ← empty set
4. FOR each token in bm25_tokens:
5.     candidates.update(tf_index[token].keys())
6. query_pairs   ← ProximityScorer.generate_query_pairs(raw_tokens)
7. scored        ← empty list
8. FOR each doc in documents WHERE doc.doc_id IN candidates:
9.     bm25       ← BM25Scorer.score(bm25_tokens, doc.doc_id)
10.    IF bm25 == 0: CONTINUE
11.    title_bonus ← count(bm25_tokens ∩ title_tokens[doc.doc_id]) × TITLE_BOOST
12.    prox_score  ← ProximityScorer.score(doc.doc_id, query_pairs, max_window=30)
13.    final       ← bm25 + title_bonus + PROXIMITY_WEIGHT × prox_score
14.    IF final > 0: scored.append((final, doc))
15. SORT scored DESCENDING by final
16. RETURN top_k entries with full metadata
```

**Edge Cases:**
- **Empty query**: Caught at controller level before reaching SearchEngine → HTTP 400.
- **Query with only stopwords** (e.g., "the and of"): BM25 processor removes stopwords → zero tokens → empty candidate set → empty results.
- **Single-token query**: No proximity pairs can be formed → `prox_score = 0.0`. Final score = BM25 + title bonus only.
- **Document with BM25 = 0**: Skipped entirely (algorithm line 10) — term exists in index but has zero TF for this doc due to tokenization mismatch.

### 6.2 Two-Phase Candidate Generation

**Phase 1 — Candidate Generation:**
- Union of all document IDs from `tf_index` that contain at least one lemmatized query token (with stopwords removed).
- This is the broadest possible recall set.

**Phase 2 — Scoring:**
- Every candidate document is scored on three dimensions.
- Documents with BM25 = 0 are excluded (token present in index but not found — edge case for stopword-mismatched tokens).
- Final sort is by combined score.

### 6.3 BM25 Scoring

```
BM25 Formula (k1=1.5, b=0.75):
  score(D, Q) = Σ IDF(t) × [tf(t,D) × (k1+1)] / [tf(t,D) + k1 × (1-b + b × |D|/avgdl)]

IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
```

- `tf(t,D)`: term frequency of term `t` in document `D`
- `df(t)`: document frequency (number of documents containing `t`)
- `N`: total number of documents
- `|D|`: length of document `D`
- `avgdl`: average document length across corpus

**Edge Cases:**
- `doc_len = 0`: Returns 0.0 immediately (no content to score).
- `df(term) = 0` (term not in any document): `idf = 0.0` via explicit guard → contributes nothing.
- `tf(term, doc) = 0`: IDF is computed but term contributes 0 to the sum.

### 6.4 Proximity Scoring

**Pair Generation Heuristic:**
- **≤ 5 query tokens**: All unordered pairs → `O(n²/2)` pairs
- **> 5 query tokens**: Adjacent pairs only (sliding window of 2) → `O(n-1)` pairs

**Distance Metric:**
- `_min_ordered_distance(pos1, pos2)`: Minimum distance where term1 occurs **before** term2.
- Two-pointer sweep over sorted position lists.

**Score Function:**
```python
score = avg(1 / (distance + 1)²) for all valid pairs
```
- Quadratic inverse: close pairs contribute much more than distant ones.
- Pairs with distance > `max_window` (default 30) are discarded.
- Terms with no co-occurrence contribute zero.

**Edge Cases:**
- **Single-token query**: `generate_query_pairs` returns `[]` → `score()` returns 0.0.
- **Same-term pair** (e.g., ("right", "right")): Explicitly skipped (self-pair adds no signal).
- **No co-occurrence in document**: `doc_id` not found in positional index for either term → pair contributes 0.
- **Distance > max_window (30)**: Pair discarded, contributes 0 to average.

### 6.5 RAG Workflow

The actual pipeline layers retrieval and LLM generation through multiple components:

**Retrieval:** `RAGRepository.retrieve()` → `RetrievalWorkflow.retrieve()` → `SearchEngine.search(query, recall_k=30)` + `Reranker.rerank(top_k=8)` → results promoted to article level.

**LLM Generation:**
```
ask(query, retrieve_only=False):

1. retrieved_articles = RAGRepository.retrieve(query, top_k=max_context_articles)
2. promoted = RAGRepository.promote_to_articles(retrieved_articles)
3. result = { query, retrieved_articles: [{doc_id, title, citation, score}], ... }

4. IF retrieve_only: RETURN result

5. context = RAGFormatter.format_context(promoted)
6. prompt  = RAGFormatter.build_prompt(query, context)
7. messages = [{role: "user", content: prompt}]

8. TRY (with RETRY_ATTEMPTS=3, RETRY_DELAY=0.5s):
9.     response = RAGRepository.call_llm(messages)
10.    result["answer"] = response.content
11.    result["citations"] = [{article, title, doc_id}]
12. EXCEPT:
13.    result["answer"] = "Error querying LLM: {error}"
14.    result["error"] = str(error)

15. RETURN result
```

### 6.6 Prompt Engineering

```
You are an expert in constitutional law, specifically the Constitution of Nepal.
Answer based ONLY on the provided constitutional articles.

CONSTITUTION ARTICLES:
[Article 1]
Citation: Part 3, Article 31
Title: Right relating to education
Content: ...

QUESTION: What is the right to education?

RULES:
- Answer strictly from provided articles only.
- Cite articles precisely as [Part X, Article Y(Z)].
- If the Constitution does not address the question, explicitly state so.
- Do not reference external knowledge.
```

### 6.7 Query Processing Flow (QAService)

```
answer_query(query, useLLM=False):

1. workflow = _get_workflow()  [lazy singleton init]

2. IF NOT useLLM:
3.     result = workflow.ask(query, retrieve_only=True)
4.     RETURN { query, articles } → 200

5. IF useLLM:
6.     connected, msg = workflow.check_ollama_connection()
7.     IF NOT connected:
8.         RETURN { error: "Ollama service unavailable." } → 503

9.     model_ok, status, available = workflow.check_model_availability()
10.    IF NOT model_ok:
11.        result = workflow.ask(query, retrieve_only=True)
12.        RETURN { query, articles, ollama_status } → 200

13.    result = workflow.ask(query, stream=False, retrieve_only=False)
14.    RETURN { query, response, articles, ollama_status } → 200
```

### 6.8 Offline Ingestion Pipeline

```
run_ingestion():
1. flatten_constitution()
   - Reads:  data/nepal_constitution_new.json
   - Output: data/output/flattened_nepal_constitution.json

2. build_index()
   - Reads:  data/output/flattened_nepal_constitution.json
   - Output: data/output/tf_index.json
             data/output/pos_index.json
             data/output/doc_stats.json

3. generate_safe_lemma_dict()
   - Reads:  data/output/flattened_nepal_constitution.json
   - Output: data/output/lemma_dict_v3.json
```

### 6.9 Text Processing Pipeline

```
process_text(text):
1. Normalize:
   - Lowercase
   - Expand contractions (57 contractions → expansions)
   - Keep only alphabetic characters and whitespace

2. Optional Lemmatization (spaCy en_core_web_sm):
   - Join tokens → spaCy Doc → extract lemma_ for each token
   - Skip spaces, punctuation
   - Handle missing lemmas ("-pron-" → original token)

3. Optional Stopword Removal (~120 stopwords)

Two Processor Configurations:
- BM25 Processor:  lemmatization=ON,  stopwords=REMOVED
- Proximity Processor: lemmatization=OFF, stopwords=KEPT
```

**Edge Cases:**
- `process_text("")` or `None`: Returns `[]` immediately.
- **spaCy model missing** (`en_core_web_sm` not installed): Falls back to `spacy.blank("en")` — tokenization works, lemmatization produces identity forms.
- **Contraction at sentence boundary** (e.g., "can't."): Alpha-only filter removes the period after expansion → "cannot" is preserved as a token.

### 6.10 JWT Authentication Flow

```
@token_required decorator:
1. Extract token from:
   - Authorization: Bearer <token> header, OR
   - token cookie
2. IF no token: RETURN 401 "Token is missing!"
3. IF JWT_SECRET not set: RETURN 500 server error
4. TRY decode with jwt.decode(token, JWT_SECRET, HS256)
5. Attach payload to request.user
6. ON jwt.ExpiredSignatureError: RETURN 401 "Token has expired!"
7. ON jwt.InvalidTokenError: RETURN 401 "Invalid token!"
```

---

## 7. Feature Breakdown

### 7.1 Implemented Features

| Feature | Status | Details |
|---------|--------|---------|
| **Hybrid Search Engine** | ✅ Complete | BM25 + term proximity + title boost in `src/core/` |
| **Offline Ingestion Pipeline** | ✅ Complete | 3-step: flatten → build indexes → lemma dict |
| **Flask API Server** | ✅ Complete | Blueprint-based routing, CORS enabled |
| **Ask Endpoint** | ✅ Complete | `POST /api/v1/ask` with full validation + graceful degradation |
| **RAG with Ollama** | ✅ Complete | Retrieval → strict prompt → LLM call with 3x retry |
| **Graceful LLM Degradation** | ✅ Complete | 3 cases: OK → answer; model missing → retrieval-only; unreachable → 503 |
| **User Authentication** | ✅ Complete | Register, login (JWT), logout, get current user |
| **JWT Decorator** | ✅ Complete | `@token_required` with Bearer header + cookie fallback |
| **React Frontend SPA** | ✅ Complete | Search, LLM toggle, suggestion pills, expandable cards, chat history, message detail |
| **Chat History API** | ✅ Complete | Full CRUD: list/get/delete messages per user with populated article refs |
| **Algorithmic Reranking** | ✅ Complete | RRF fusion + MMR diversity + rule-based boost via `Reranker` |
| **Automated Tests** | ✅ Partial | Unit + integration tests at `backend/temp/tests/` |

### 7.2 Known Gaps (Scope Decisions)

| Gap | Status | Reason |
|-----|--------|--------|
| **Admin API routes** | ❌ Not exposed | `UserService.list_users()` / `delete_user()` exist but no admin blueprint |
| **Async/sync mismatch in services** | ⚠️ Misleading | `message_service.py`/`article_service.py` use `async def` with sync `mongoengine` (not broken, functionally correct) |
| **CORS hardening** | ⚠️ Permissive | `CORS(app)` with no restrictions in `app.py:19` |
| **Observability** | ❌ Missing | No latency tracking, structured logging, or request metrics |
| **Retrieval-only endpoint** | ❌ Not dedicated | `/ask?use_llm=false` works but no dedicated `/api/v1/search` |
| **Multi-model fallback** | ❌ Not implemented | If `gemma3:1b` unavailable, no automatic fallback to alternative models |

### 7.3 Out of Scope (Academic Project)

The following production-grade concerns are intentionally excluded — they do not affect the core system behavior or academic contribution:
CI/CD pipeline, Docker/containerization, rate limiting, structured logging/tracing, multi-language support, WSGI deployment, frontend state management library (Redux/Zustand), Python linter/formatter.

---

## 8. Setup & Environment

### 8.1 Prerequisites

- Python 3.13+
- Node.js 22+ (for frontend)
- MongoDB 8.0+ (local or remote)
- Ollama (for LLM features) — [ollama.ai](https://ollama.ai)

### 8.2 Quick Start

**1. Clone and navigate:**
```bash
cd backend
```

**2. Create and activate virtual environment:**
```powershell
# PowerShell
.venv\Scripts\Activate.ps1
```

**3. Install Python dependencies:**
```powershell
pip install -r requirements.txt
```
> ⚠️ `requirements.txt` is UTF-16 encoded. If tools misread it, save a UTF-8 copy.

**4. Configure environment:**
```bash
cp .env.sample .env
# Edit .env with your values
```

**5. Start MongoDB** (ensure `mongod` is running on `localhost:27017`)

**6. Start Ollama** (ensure model is pulled):
```bash
ollama serve
ollama pull gemma3:1b
```

**7. Build indexes (first time only):**
```powershell
python app.py --rebuild-data
```

**8. Start the API server:**
```powershell
python app.py
```
Server starts on `http://127.0.0.1:5000`

**9. Start the frontend (separate terminal):**
```bash
cd frontend
npm install
npm run dev
```
Frontend starts on `http://localhost:5173`

### 8.3 Environment Variables

From `backend/.env`:

| Variable | Default | Required | Description |
|----------|---------|:--------:|-------------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | No | Ollama server URL |
| `OLLAMA_API_KEY` | (empty) | No | Bearer token for Ollama auth |
| `OLLAMA_MODEL` | `gemma3:1b` | No | Default LLM model name |
| `MONGO_URI` | `mongodb://localhost:27017` | No | MongoDB connection string |
| `MONGO_DB_NAME` | `ECIRAS` | No | Database name (set in code, not .env) |
| `JWT_SECRET` | (must set) | **Yes** | HS256 signing key for JWT tokens |

### 8.4 Dependency List

**Python (backend/requirements.txt — UTF-16 encoded):**

| Package | Purpose |
|---------|---------|
| flask | Web framework |
| flask-cors | Cross-Origin Resource Sharing |
| mongoengine | MongoDB ODM |
| pymongo | MongoDB driver |
| spacy | NLP (lemmatization, tokenization) |
| en_core_web_sm | spaCy English model |
| ollama | Ollama LLM client |
| bcrypt | Password hashing |
| PyJWT | JSON Web Token handling |
| python-dotenv | Environment variable loading |
| PyPDF2 | PDF parsing |
| nltk | Natural Language Toolkit |
| torch | PyTorch |
| httpx | HTTP client |
| typer | CLI framework |
| rich | Terminal formatting |

**Frontend (package.json):**

| Package | Purpose |
|---------|---------|
| react 19 | UI library |
| react-dom 19 | React DOM renderer |
| tailwindcss 4 | Utility CSS framework |
| @tailwindcss/vite | Tailwind Vite plugin |
| @vitejs/plugin-react | Vite React plugin |
| vite 8 | Build tool / dev server |
| eslint | Linting |
| pptxgenjs | PPTX generation (installed but unused) |

### 8.5 Useful Commands

```powershell
# Backend
python app.py                          # Start server
python app.py --rebuild-data           # Rebuild indexes + start server
python -m preprocessing_scripts.run_ingestion  # Manual full pipeline
python -m preprocessing_scripts.build_index     # Indexes only
python -m src.llm.rag_workflow         # Run RAG demo

# Frontend
npm run dev                            # Dev server with HMR
npm run build                          # Production build
npm run lint                           # ESLint check
npm run preview                        # Preview production build

# Both
# From project root:
# Open two terminals:
# Terminal 1: python backend/app.py
# Terminal 2: cd frontend && npm run dev

# Or use Makefile:
make backend    # Start backend
make frontend   # Start frontend
make run        # Start both (separate windows)
```

---

## 9. Known Limitations

### 9.1 Resolved Bugs

The following bugs were identified during documentation review and have been fixed:

| # | Bug | Fix Applied |
|---|-----|-------------|
| 1 | `query_iscontains` typo in `message_service.py:152` — should be `query__icontains` | ✅ Changed to `query__icontains` |
| 2 | `register()` / `login()` called `.strip()` on `data.get()` without null guard | ✅ Wrapped with `(data.get("field") or "")` |

### 9.2 Scope Decisions

| Decision | Detail |
|----------|--------|
| **Message persistence wired** | `MessageService` + `ArticleService` are used by `_persist_message()` in both `/ask` and `/ask-stream`. Queries, LLM answers, and article references are saved per user. |
| **`/me` response nesting** | Response wraps `UserService.get_user()` output inside `"user"` key — service dict (`success`/`data`/`message`) appears nested. Works correctly but adds one level of indirection. |
| **`/ask` authenticated** | Auth system is functional and `/ask` requires `@token_required`. |
| **`to_json()` excludes role** | `User.to_json()` returns id, fullname, email, timestamps — role is excluded by design for default serialization. |

### 9.3 Cleanup Notes

- `frontend/src/App.css` contains ~150 lines of unused Vite boilerplate CSS.
- `frontend/package.json` lists `pptxgenjs` as a dependency that is never imported.
- `backend/app_bootstrap.py:12` log message mentions `data/nepal_constitution.json` but the actual script reads `data/nepal_constitution_new.json`.

---

## 10. Appendix: Mermaid Diagrams

Mermaid diagram sources and rendered outputs are in `docs/mermaid/`.

### Available Diagrams

| Diagram | File | Description |
|---------|------|-------------|
| System Architecture | `inputs/sys_architecture.mmd` | High-level component relationship |
| Workflow | `inputs/work_flow.mmd` | Offline ingestion + online retrieval |
| Class Diagram | `inputs/class_diagram.mmd` | Core class relationships |
| Sequence Diagram | `inputs/sequence_diagram.mmd` | Full Q&A request flow |
| Component Diagram | `inputs/component_diagram.mmd` | Deployment component view |
| Activity Diagram | `inputs/activity_diagram.mmd` | Process flow |
| State Diagram | `inputs/state_diagram.mmd` | System states |
| Object Diagram | `inputs/object_diagram.mmd` | Object relationships |
| Deployment Diagram | `inputs/deployment_diagram.mmd` | Physical deployment topology |

### Rendering

Open the `.mmd` files at [mermaid.live](https://mermaid.live) or use the render script:
```batch
docs\mermaid\render.bat
```
Outputs as `.svg` and `.png` in `docs/mermaid/outputs/`.

---

## 11. Design Decisions (Rationale)

### 11.1 Why RAG instead of pure LLM?

Legal question-answering demands **factual grounding**. A pure LLM can generate plausible-sounding but incorrect citations (hallucination). RAG forces the LLM to answer strictly from retrieved articles, with explicit citations. This is essential for legal contexts where incorrect answers have real consequences.

### 11.2 Why two text processors?

| Processor | Lemmatization | Stopwords | Purpose |
|-----------|:-------------:|:---------:|---------|
| BM25 | ON | REMOVED | Term frequency matching benefits from normalization — "rights" and "right" should match. Stopwords add noise to IDF. |
| Proximity | OFF | KEPT | Phrase proximity preserves original word order — "right to education" ≠ "education right". Stopwords are structural for distance. |

A single processor cannot serve both purposes.

### 11.3 Why the proximity pair heuristic?

| Query length | Strategy | Complexity | Rationale |
|:------------:|----------|:----------:|-----------|
| ≤ 5 tokens | All unordered pairs | O(n²/2) | Short queries benefit from full cross-term proximity |
| > 5 tokens | Adjacent pairs only | O(n−1) | Distant term pairs in long queries contribute negligible signal; adjacent pairs capture key phrase structure |

This heuristic is supported by IR research showing that phrase-level proximity matters most for adjacent or near-adjacent terms.

### 11.4 Why lazy singleton for QAService?

- **spaCy** (`en_core_web_sm`) takes ~1–2 seconds to load.
- **Index files** (tf_index, pos_index, doc_stats) are ~5 MB combined and require parsing.
- **Retrieval pipeline** (SearchEngine, Reranker, RetrievalWorkflow, RAGRepository, RAGWorkflow) is assembled on first request.
- Lazy initialization means the server starts immediately; the first query pays the one-time load cost.
- Double-checked locking (`_workflow_lock`) ensures thread safety without locking on every request.

### 11.5 Why is `/ask` authenticated?

All Q&A endpoints (`/ask`, `/ask-stream`, and message management) require JWT authentication via the `@token_required` decorator. This enables per-user message persistence and prevents anonymous usage. The auth system uses httpOnly secure SameSite=Strict cookies with Bearer header fallback.

### 11.6 Why is message persistence wired to `/ask`?

Persistence is wired via `_persist_message()` in `api_controller.py`, which calls `ArticleService.create_article()` for each retrieved article and `MessageService.create_message()` to save the query/answer pair. This was implemented to support the chat history feature — users can review past Q&A sessions through the frontend. The service layer separation ensures the Q&A logic itself remains independent of any storage backend.

### 11.7 Failure Mode Summary

| Failure | Behavior | User Sees |
|---------|----------|-----------|
| MongoDB offline | Server crashes on startup (intentional fail-fast) | Connection error on server start |
| Ollama not running, `use_llm=true` | Detection → HTTP 503 | `{"error": "Ollama service is unavailable."}` |
| Ollama running, model not pulled | Detection → HTTP 200 + articles | `ollama_status.model_available=false` |
| LLM call fails mid-generation after 3 retries | Catches exception → HTTP 200 | `response` field contains error text; `error` field set |
| Invalid JSON payload | Validation → HTTP 400 | `{"error": "Invalid JSON payload."}` |
| Query > 500 characters | Validation → HTTP 400 | `{"error": "Query is too long..."}` |
| spaCy model missing (`en_core_web_sm`) | Falls back to blank `en` | Tokenization works; lemmatization becomes identity |

---

*Document generated by codebase analysis. All assumptions explicitly marked with `[Assumption]`.*
