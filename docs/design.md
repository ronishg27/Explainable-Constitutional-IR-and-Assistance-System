# Constitution Assistant — Design Document

## 1. Overview

**Constitution Assistant** is a Retrieval-Augmented Generation (RAG) system that answers natural-language questions about the Constitution of Nepal (2072 / 2015). Users ask legal questions in plain English, and the system returns relevant constitutional articles ranked by a custom hybrid search engine, optionally enhanced with an LLM-generated answer grounded strictly in the retrieved provisions.

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React 19 + Vite 8)             │
│                                                              │
│  App                                                         │
│  ├── Navbar               — Top navigation with branding     │
│  ├── ProtectedRoute       — Auth gate (redirects to login)   │
│  ├── HomePage             — Main search interface            │
│  │   └── MainSearchBar    — Input + LLM toggle + submit      │
│  │       ├── Suggestion   — 6 preset query pills             │
│  │       └── Resultdisplay— Answer + article cards            │
│  │           ├── ArticleCard (expandable, per result)        │
│  │           └── ConfidenceBadge                             │
│  ├── LoginPage / RegisterPage                                │
│  ├── HistoryPage          — Paginated chat history           │
│  ├── MessageDetailPage    — Single Q&A detail view            │
│  ├── AboutPage / HowItWorksPage / NotFoundPage               │
│                                                              │
│  State: AuthProvider → apiClient → localStorage JWT          │
│  Streaming: useAskStream (SSE via ReadableStream)            │
└───────────────────────────┬─────────────────────────────────┘
                            │ POST /api/v1/ask (JWT Bearer)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Flask / Python 3.13)              │
│                                                              │
│  ┌──────────┐  ┌────────────┐  ┌─────────────────────────┐ │
│  │  Routes   │  │Controllers │  │      Services            │ │
│  │(Blueprints)│  │(validation)│  │  QAService (singleton)   │ │
│  └──────────┘  └────────────┘  └──────────┬──────────────┘ │
│                                            │                │
│                    ┌───────────────────────┼───────────┐    │
│                    │     RAGWorkflow       │           │    │
│                    │  ┌─────────────────┐  │           │    │
│                    │  │  RAGRepository   │  │           │    │
│                    │  │  (retrieval +    │  │           │    │
│                    │  │   Ollama client)  │  │           │    │
│                    │  └────────┬────────┘  │           │    │
│                    │           │           │           │    │
│                    │  ┌────────▼────────┐  │           │    │
│                    │  │RetrievalWorkflow │  │           │    │
│                    │  └─────┬──────┬────┘  │           │    │
│                    │        │      │       │           │    │
│                    │  ┌─────▼──┐ ┌──▼──────┐          │    │
│                    │  │Search  │ │Reranker │          │    │
│                    │  │Engine  │ │(RRF+MMR │          │    │
│                    │  │BM25+prx│ │ +boost) │          │    │
│                    │  └────────┘ └─────────┘          │    │
│                    └──────────────────────────────────┘    │
│                                                              │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐ │
│  │  Config       │  │   Models ODM   │  │  Preprocessing   │ │
│  │ (MongoDB)     │  │(User/Message/  │  │  (flatten +      │ │
│  │  Singleton)   │  │  Article)      │  │   index build)   │ │
│  └──────────────┘  └────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │      MongoDB 8            │
              │  ECIRAS database          │
              │  users / messages /       │
              │  referenced_articles       │
              └───────────────────────────┘
```

## 3. Tech Stack

| Layer     | Technology                  | Details                                                 |
| --------- | --------------------------- | ------------------------------------------------------- |
| Backend   | Python 3.13 + Flask         | Flask with CORS, Blueprints                             |
| Frontend  | React 19 + Vite 8           | Tailwind CSS v4, JSX                                    |
| Database  | MongoDB 8 (mongoengine ODM) | Users, messages, article refs                           |
| IR Engine | Custom Python               | BM25 + term proximity + title boost + RRF/MMR reranking |
| NLP       | spaCy (`en_core_web_sm`)    | Lemmatization, tokenization                             |
| LLM       | Ollama (local)              | Default: `qwen2.5:7b`                                   |
| Auth      | JWT (HS256, 12h expiry)     | Bearer header + httpOnly cookie fallback                |
| Tooling   | Prettier, ESLint, Vite HMR  |                                                         |

## 4. Layer Details

### 4.1 Backend Layered Architecture

```
app.py → routes/ (Blueprints) → controllers/ (validation) → services/ (orchestration)
                                                                ↓
                                                          src/core/ (retrieval)
                                                          src/llm/ (RAG)
                                                                ↓
                                                          config/ (MongoDB)
                                                          models/ (ODM)
```

- **Routes** (`routes/api_routes.py`, `routes/auth_routes.py`): Flask Blueprints that define URL mappings.
- **Controllers** (`controllers/api_controller.py`, `controllers/auth_controller.py`): Input validation, request parsing, response formatting.
- **Services** (`services/qa_service.py`, `services/user_service.py`, etc.): Business logic orchestration. `QAService` implements a lazy singleton pattern (double-checked locking) for `RAGWorkflow` initialization.
- **Core** (`src/core/`): Pure retrieval logic with no Flask dependency. Testable in isolation.
- **LLM** (`src/llm/`): RAG orchestration, prompt building, Ollama client.
- **Decorators** (`controllers/decorators.py`): `@token_required` — extracts JWT from `Authorization: Bearer` header (primary) or `token` cookie (fallback), decodes with HS256, checks `token_version` against the user document for token invalidation.

### 4.2 Frontend Component Tree

```
App (BrowserRouter)
├── Navbar               — Sticky top nav with "Constitutional Assistant" branding
│                          Desktop: Home, About, How It Works, History, Logout
│                          Mobile: hamburger menu with same links
├── ProtectedRoute       — Spinner while auth loads, redirects to /login if not auth'd
│
├── / → HomePage
│   └── MainSearchBar    — Search input + Cancel button + AI toggle + Suggestion pills
│       ├── Suggestion   — 6 preset query buttons (President election, rights, etc.)
│       ├── useAskStream — Custom hook managing SSE state (articles, response, loading, error)
│       └── Resultdisplay— Two-column: answer (markdown) + article cards
│           ├── ArticleCard  — Expandable card: rank, title, citation, score badge, tags
│           │                  Expanded: full text with term highlighting + breakdown
│           └── ConfidenceBadge — Colored badge: green ≥70%, amber ≥40%, red <40%
│
├── /login → LoginPage
├── /register → RegisterPage
├── /history → HistoryPage (paginated, delete single + clear all)
├── /history/:id → MessageDetailPage
├── /about → AboutPage (static)
├── /how-it-works → HowItWorksPage (4-step process)
└── * → NotFoundPage (404)

UI Primitives (components/ui/):
  Button (primary/secondary/danger/ghost, sm/md/lg, loading)
  Input (floating label, error state, helper text)
  Toggle (role="switch", keyboard support)
  Card (optional header/footer)
  Alert (error/success/warning/info, dismissible)
  Badge, Spinner, Pagination, Dialog (modal)
```

### 4.3 Auth Flow

```
Login → POST /api/v1/auth/login
  ├─ Backend: UserService.authenticate_user() → JWT (HS256, 12h, payload: user_id, email, token_version)
  ├─ Sets httpOnly cookie (Secure in production, SameSite=Strict)
  ├─ Returns token in response body
  └─ Frontend stores token in localStorage, sends as Authorization: Bearer header

Every request → @token_required:
  1. Try Authorization: Bearer <token> header
  2. Fallback to token cookie
  3. Decode JWT, compare token_version against user document in MongoDB
  4. Attach decoded payload to request.user

Logout:
  1. Increments user.token_version in MongoDB (invalidates all existing JWTs)
  2. Clears cookie (max_age=-1)

Register → POST /api/v1/auth/register:
  - Validates: fullname (3-50 chars), email (regex), password (min 6), role (user/admin)
  - Bcrypt hashing via User.set_password()
```

## 5. Retrieval Pipeline

### 5.1 Two-Phase Retrieval Pipeline

The `SearchEngine` (`src/core/search_engine.py`) implements candidate-generation + scoring, followed by `Reranker` (RRF fusion + MMR diversity + rule-based boost). The full chain:

```
Query → [BM25 Processor]  ──→ bm25_tokens (lemmatized, no stopwords)
     → [Proximity Processor] ──→ raw_tokens (exact, stopwords kept)
                                       │
                                       ▼
                            Synonym Expansion (optional)
                            44 groups from data/synonyms.json
                            (e.g., "arrest/detention/custody")
                                       │
                                       ▼
                            Candidate Generation (recall_k=30)
                            (union of doc IDs containing any bm25 token)
                                       │
                                       ▼
                            For each candidate document:
                              score = BM25(k1=1.5, b=1.0)
                                    + title_boost (×5.0 per title token match)
                                    + proximity_weight (×1.0 × avg pair score)
                                       │
                                       ▼
                            Top-30 candidates
                                       │
                                       ▼
                            Reranker.rerank():
                              1. RRF Fusion (combine BM25 + proximity + title ranks)
                              2. MMR Diversity (cosine similarity via BM25 TF vectors)
                              3. Rule-based Boost (doc.boost * part_rules * level_rules)
                                       │
                                       ▼
                            Top-8 articles → Article Promotion
                            (clause/sub-clause merged to article level,
                             deduplicated by article_no)
                                       │
                                       ▼
                            (Optional) LLM Generation via Ollama
                              - Context truncated to matched clauses only
                              - Strict grounding prompt
                              - 3 retries with 0.5s delay
                              - 4096 context window
```

### 5.2 BM25 Scoring

Implementation: `src/core/bm25_scorer.py`

Standard BM25 formula with `k1=1.5`, `b=1.0`:

$$
\text{score}(D, Q) = \sum_{t \in Q} \text{IDF}(t) \times
\frac{\text{tf}(t, D) \times (k_1 + 1)}
     {\text{tf}(t, D) + k_1 \times \left(1 - b + b \times \dfrac{|D|}{\text{avgdl}}\right)}
$$

$$
\text{IDF}(t) = \log\left(\frac{N - \text{df}(t) + 0.5}{\text{df}(t) + 0.5} + 1\right)
$$

### 5.3 Proximity Scoring

Implementation: `src/core/proximity.py`

- **Pair generation heuristic**: ≤5 query tokens → all unordered pairs; >5 tokens → adjacent pairs only.
- **Distance metric**: Minimum ordered distance between term occurrences (two-pointer sweep).
- **Score function**: average over all pairs — quadratic inverse so close pairs contribute much more.

$$
\text{score}_{\text{pair}}(a, b) = \frac{1}{(d(a, b) + 1)^2}
$$
- **Window cap**: Pairs farther than 30 tokens are discarded.

### 5.4 Two Text Processors

The engine maintains separate `TextProcessor` instances (`src/core/text_processor.py`):

| Processor           | Lemmatization | Stopwords | Used For                            |
| ------------------- | :-----------: | :-------: | ----------------------------------- |
| bm25_processor      |      ON       |  REMOVED  | Candidate generation & BM25 scoring |
| proximity_processor |      OFF      |   KEPT    | Proximity pair matching             |

Pipeline steps: Normalize (lowercase → expand 57 contractions → alpha-only filter) → Optional lemmatization (spaCy `en_core_web_sm`, falls back to `spacy.blank("en")`) → Optional stopword removal.

### 5.5 Synonym Expansion

Implementation: `src/core/query_expander.py`

- Loads 44 synonym groups from `data/synonyms.json`
- Applied to BM25 tokens only (not proximity tokens)
- Multi-word phrases (e.g., "right to privacy") only included if present in the raw query string
- Applied in `SearchEngine.search()` when the `synonym_expander` parameter is set (via `EngineFactory`)

### 5.6 Reranking (Reranker)

Implementation: `src/core/reranker.py`

Three stages, purely algorithmic (no ML/embeddings):

| Stage | Method                  | Purpose                                                                                                             |
| :---: | ----------------------- | ------------------------------------------------------------------------------------------------------------------- |
|  2a   | RRF Fusion (`k=60`)     | Combine BM25, proximity, and title-match rankings into a single fused score                                         |
|  2b   | MMR Diversity (`λ=0.5`) | Re-rank to maximize relevance + diversity (cosine similarity on BM25 TF vectors)                                    |
|  2c   | Rule-based Boost        | Apply per-document boost, part-level multipliers, and level multipliers (article=0.98, clause=0.95, subclause=0.90) |

### 5.7 Article Promotion

Implementation: `src/llm/rag_repository.py`

After reranking, clause/sub-clause results are promoted to article level:

1. **Group** all documents by `article_no`
2. For articles with a top-level text (lettered sub_clauses) → use directly
3. For articles stored as individual numbered clauses → concatenate all clause texts
4. **Deduplicate** by `article_no` (keep highest-scoring entry)
5. Track which specific clauses matched for context truncation
6. `build_truncated_text()` returns only the matched clause texts for LLM context efficiency

## 6. RAG Pipeline

### 6.0 Prompt Construction (`src/llm/rag_formatter.py`)

- System prompt: strict grounding — "Answer ONLY using the Context"
- User prompt: `Context: ... Question: ... Task: ... Answer:`
- If answer not in context, explicitly state so

### 6.1 LLM Integration

- **Client**: `RAGRepository` owns the `ollama.Client` (Python SDK)
- **Default model**: `qwen2.5:7b` (configurable via `OLLAMA_MODEL` env var)
- **Connectivity**: Cached per process lifetime, first request initiates check
- **Retry**: 3 attempts with 0.5s delay, 4096 context window, `keep_alive=30m`
- **Fallback**: unreachable → 503; model missing → retrieval-only with status info

### 6.2 Q&A Endpoint Behavior

| `use_llm` | Ollama State              | Status | Response                                       |
| :-------: | ------------------------- | :----: | ---------------------------------------------- |
|  `false`  | —                         |  200   | Ranked articles only                           |
|  `true`   | Connected + model loaded  |  200   | LLM answer + article citations + ollama_status |
|  `true`   | Connected + model missing |  200   | Retrieval-only + ollama_status (no LLM answer) |
|  `true`   | Unreachable               |  503   | Error: "Ollama service is unavailable."        |
|  `true`   | LLM fails after retries   |  200   | Error text in answer + error field             |

## 7. Offline Ingestion Pipeline

### 7.1 Pipeline Steps

```
Source JSON (nested constitution: data/nepal_constitution_new.json)
        │
        ▼
flatten_constitution.py  ──→ flattened_nepal_constitution.json (~700+ flat docs)
        │                   Handles two input formats: nested (parts→articles→clauses)
        │                   and flat list format
        ▼
IngestionWorkflow (index_builder.py)
  ├── build_tf_index()        → tf_index.json   (term → {doc_id: tf})
  ├── build_positional_index()→ pos_index.json   (term → {doc_id: [positions]})
  └── compute_doc_stats()     → doc_stats.json   (doc_lengths + avgdl)
        │
        ▼
generate_safe_lemma_dict.py ──→ lemma_dict_v3.json (rule-based corpus lemmas,
                                no spaCy dependency: -ies, -es, -s, -ing, -ed,
                                -er, -est + irregular forms)
```

### 7.2 Running the Pipeline

- `python app.py --rebuild-data` — full rebuild on server start
- `python -m preprocessing_scripts.run_ingestion` — manual pipeline
- `python -m preprocessing_scripts.build_index` — indexes only from existing flattened JSON

## 8. Data Models (MongoDB via mongoengine)

### User (`users` collection)

| Field           | Type     | Constraints             | Description              |
| --------------- | -------- | ----------------------- | ------------------------ |
| `fullname`      | String   | required, min=3, max=50 | Display name             |
| `email`         | String   | required, unique        | Login identifier         |
| `password_hash` | String   | required                | bcrypt hash              |
| `role`          | Enum     | default=`user`          | `user` / `admin`         |
| `token_version` | Int      | default=0               | JWT invalidation counter |
| `created_at`    | DateTime | auto-set                |                          |
| `updated_at`    | DateTime | auto-updated            |                          |

**Methods:** `set_password()`, `check_password()`, `to_json()` (excludes password_hash, role)

### Message (`messages` collection)

| Field        | Type                           | Constraints       | Description                            |
| ------------ | ------------------------------ | ----------------- | -------------------------------------- |
| `query`      | String                         | required          | User question                          |
| `answer`     | String                         | optional          | LLM response (empty if retrieval-only) |
| `user`       | Reference(User)                | CASCADE on delete | Owner                                  |
| `articles`   | List\[Ref(ReferencedArticle)\] | NULLIFY on delete | Referenced articles                    |
| `created_at` | DateTime                       | auto-set          |                                        |
| `updated_at` | DateTime                       | auto-updated      |                                        |

### ReferencedArticle (`referenced_articles` collection)

| Field                 | Type           | Constraints    | Description                              |
| --------------------- | -------------- | -------------- | ---------------------------------------- |
| `title`               | String         | required       | Article title                            |
| `citation`            | String         | required       | e.g., "Part 3, Article 31"               |
| `doc_id`              | String         | required       | Unique document ID from flattened corpus |
| `relevance_score`     | Float          | required, ≥0.0 | Combined final score                     |
| `bm25_score`          | Float          | default=0.0    | Raw BM25 component                       |
| `proximity_score`     | Float          | default=0.0    | Raw proximity component                  |
| `title_match_count`   | Int            | default=0      | Query terms matched in title             |
| `article_no`          | Int            | optional       | Corresponding article number             |
| `clause_no`           | String         | optional       | Corresponding clause label               |
| `subclause_id`        | String         | optional       | Sub-clause identifier                    |
| `level`               | String         | optional       | `"article"`, `"clause"`, `"subclause"`   |
| `part_no`             | Int            | optional       | Corresponding part number                |
| `text`                | String         | optional       | Truncated text for LLM context           |
| `full_text`           | String         | optional       | Full provision text                      |
| `matched_terms`       | List\[String\] | default=\[]    | BM25-matched terms (lemmatized)          |
| `exact_matched_terms` | List\[String\] | default=\[]    | Exact-match terms (for highlighting)     |
| `created_at`          | DateTime       | auto-set       |                                          |
| `updated_at`          | DateTime       | auto-updated   |                                          |

### Entity Relationships

```
User (1) ─────── creates ──────→ Message (0..*)
Message (0..*) ── references ──→ ReferencedArticle (0..*)
```

- Deleting a User CASCADE-deletes their Messages
- Deleting a ReferencedArticle NULLIFYs the reference in Messages

## 9. API Endpoints

| Method | Path                    | Auth | Description                                        |
| ------ | ----------------------- | :--: | -------------------------------------------------- |
| GET    | `/api/v1`               |  No  | API landing + endpoint list                        |
| GET    | `/api/v1/health`        |  No  | Liveness check                                     |
| POST   | `/api/v1/ask`           | Yes  | Main Q&A (`query`, `use_llm`, persists to MongoDB) |
| POST   | `/api/v1/ask-stream`    | Yes  | Streaming Q&A via SSE                              |
| GET    | `/api/v1/messages`      | Yes  | Paginated chat history (limit, skip)               |
| GET    | `/api/v1/messages/<id>` | Yes  | Single message + articles                          |
| DELETE | `/api/v1/messages/<id>` | Yes  | Delete message (owner only)                        |
| DELETE | `/api/v1/messages`      | Yes  | Delete all messages                                |
| POST   | `/api/v1/auth/register` |  No  | User registration                                  |
| POST   | `/api/v1/auth/login`    |  No  | Login, returns JWT + sets cookie                   |
| POST   | `/api/v1/auth/logout`   | Yes  | Invalidates token (increments token_version)       |
| GET    | `/api/v1/auth/me`       | Yes  | Current user info                                  |

## 10. Database Persistence Flow

When a Q&A request succeeds (`status == 200`), `_persist_message()` in `api_controller.py`:

1. Iterates over every article in the response
2. Calls `ArticleService.create_article()` — upserts by `doc_id` (updates if exists, creates if new)
3. Collects the MongoDB ObjectIds of all created/updated articles
4. Calls `MessageService.create_message()` — saves the query, LLM answer, and article references

Failures in persistence are **logged but never break the response** (fire-and-forget).

## 11. Configuration

Environment variables (from `backend/.env`):

| Variable         | Default                     | Description               |
| ---------------- | --------------------------- | ------------------------- |
| `OLLAMA_HOST`    | `http://127.0.0.1:11434`    | Ollama server             |
| `OLLAMA_API_KEY` | (empty)                     | Bearer token for Ollama   |
| `OLLAMA_MODEL`   | `qwen2.5:7b`                | LLM model name            |
| `MONGO_URI`      | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME`  | `ECIRAS`                    | Database name             |
| `JWT_SECRET`     | _(required)_                | HS256 signing key         |

## 12. Design Decisions

### 12.1 Hybrid Scoring (BM25 + Proximity + Title Boost)

Combining bag-of-words relevance (BM25) with phrase-level closeness (proximity) and structural metadata (title boost) compensates for each method's weaknesses.

### 12.2 Dual Text Processors

Separate processors for BM25 (lemmatized, no stopwords) and proximity (raw, stopwords kept): lemmatization improves BM25 recall, stopwords hurt BM25 precision but carry positional information for proximity.

### 12.3 Proximity Pair Heuristic

Short queries (≤5 tokens) use all unordered pairs for full cross-term proximity; longer queries use adjacent pairs only to avoid O(n²) explosion.

### 12.4 Lazy Singleton Initialization

`QAService._get_workflow()` uses double-checked locking to build the `SearchEngine` (three loaded index files) only on the first API request. Keeps server startup fast.

### 12.5 Strict RAG Grounding

System prompt explicitly instructs the LLM to answer only from provided articles, cite precisely, and decline if the constitution does not address the question.

### 12.6 Graceful LLM Degradation

If Ollama is unreachable or the model is missing, the API falls back to retrieval-only mode with informative status messages. Three outcomes: answer (200), retrieval-only with status (200), or Ollama unavailable (503).

### 12.7 Token Version Invalidation

On logout, `User.token_version` is incremented in MongoDB. The `@token_required` decorator compares the `token_version` in the JWT payload against the user document — all existing JWTs become invalid immediately, not just the current session.

## 13. File / Index Artifacts

All generated in `backend/data/output/`:

| File                                | Purpose                                                    |
| ----------------------------------- | ---------------------------------------------------------- |
| `flattened_nepal_constitution.json` | ~700+ flat documents (all articles, clauses, sub-clauses)  |
| `tf_index.json`                     | Term → {doc_id: term frequency} for BM25                   |
| `pos_index.json`                    | Term → {doc_id: [positions]} for proximity scoring         |
| `doc_stats.json`                    | Document lengths + average document length                 |
| `lemma_dict_v3.json`                | Custom rule-based lemma map for corpus-specific vocabulary |
