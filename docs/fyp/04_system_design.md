# Chapter 4: System Design

## 4.1 System Architecture

The system follows a three-tier architecture with a clear separation of concerns:

**Presentation Tier**: React 19 Single-Page Application
**Application Tier**: Flask RESTful API
**Data Tier**: MongoDB 8 + File-based Indexes

```
┌──────────────────────────────────────────────────────────────────┐
│                     Presentation Tier                             │
│  React 19 SPA (Vite 8)                                           │
│  AuthProvider → localStorage JWT → Bearer header                 │
│  Pages: Home, Login, Register, History, MessageDetail,          │
│         About, HowItWorks, NotFound                              │
│  Components: Navbar, MainSearchBar, Resultdisplay, ArticleCard,  │
│              Suggestion, ConfidenceBadge, ProtectedRoute         │
│  Primitives: Button, Input, Toggle, Card, Alert, Badge,         │
│              Spinner, Pagination, Dialog                          │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS REST / SSE
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Application Tier                              │
│  Flask (Python 3.13)                                              │
│                                                                   │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  Routes   │  │  Controllers  │  │  Services                │   │
│  │(Blueprints)│  │ (validation,  │  │  QAService (singleton)   │   │
│  │            │  │  response)    │  │  UserService             │   │
│  └──────────┘  └──────────────┘  │  MessageService           │   │
│                                  │  ArticleService            │   │
│                                  └──────────┬───────────────┘   │
│                                             │                    │
│  ┌──────────────────────────────────────────┼───────────────┐   │
│  │  RAGWorkflow (orchestrator)              │               │   │
│  │  ├── RAGRepository (retrieval + LLM)     │               │   │
│  │  │   ├── RetrievalWorkflow               │               │   │
│  │  │   │   ├── SearchEngine (BM25+prox)    │               │   │
│  │  │   │   └── Reranker (RRF+MMR+boost)    │               │   │
│  │  │   └── Ollama Client (3× retry)        │               │   │
│  │  └── RAGFormatter (prompts)              │               │   │
│  └──────────────────────────────────────────┘               │   │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Data Tier                                     │
│  MongoDB 8                     File System (data/output/)         │
│  Database: ECIRAS              ├── flattened_nepal_constitution   │
│  ├── users                     ├── tf_index.json                  │
│  ├── messages                  ├── pos_index.json                 │
│  └── referenced_articles       ├── doc_stats.json                 │
│                                └── lemma_dict_v3.json             │
└──────────────────────────────────────────────────────────────────┘
```

## 4.2 Component Design

### 4.2.1 Backend Layered Architecture

The backend follows a strict layered dependency chain:

```
app.py
  → routes/ (Flask Blueprints — URL routing only)
    → controllers/ (input validation, response formatting)
      → services/ (business logic orchestration)
        → src/workflows/ (retrieval pipeline composition)
          → src/core/ (pure retrieval engine, no Flask dependency)
          → src/llm/ (RAG orchestration, Ollama client)
```

**Dependency rule**: Each layer may only depend on the layer directly below it. The `src/core/` module has no imports from Flask, enabling it to be tested and used independently.

### 4.2.2 Frontend Component Hierarchy

```
<App>
  <AuthProvider>
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
        <Route path="/history/:id" element={<ProtectedRoute><MessageDetailPage /></ProtectedRoute>} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/how-it-works" element={<HowItWorksPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  </AuthProvider>
</App>
```

**Data flow**: User input flows from `MainSearchBar` → `apiClient` (HTTP) → backend → response → `useAskStream` (SSE stream) → `Resultdisplay` (render articles + answer).

## 4.3 Database Design

### 4.3.1 Database: ECIRAS

Three collections managed by mongoengine ODM:

#### Collection: `users`
| Field | Type | Constraints |
|-------|------|-------------|
| `_id` | ObjectId | auto |
| `fullname` | String | required, min_length=3, max_length=50 |
| `email` | String | required, unique |
| `password_hash` | String | required (bcrypt) |
| `role` | Enum('user', 'admin') | default='user' |
| `token_version` | Int | default=0 |
| `created_at` | DateTime | auto-set |
| `updated_at` | DateTime | auto-updated |

**Indexes**: `email` (unique), `(fullname, created_at)`
**Ordering**: `-created_at`

#### Collection: `messages`
| Field | Type | Constraints |
|-------|------|-------------|
| `_id` | ObjectId | auto |
| `query` | String | required |
| `answer` | String | optional |
| `user` | Reference(User) | required, CASCADE on delete |
| `articles` | List\[Ref(ReferencedArticle)\] | default=[], NULLIFY on delete |
| `created_at` | DateTime | auto-set |
| `updated_at` | DateTime | auto-updated |

**Indexes**: `query`, `user`, `(query, created_at)`
**Ordering**: `-created_at`

#### Collection: `referenced_articles`
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `_id` | ObjectId | auto | |
| `title` | String | required | Article title |
| `citation` | String | required | e.g., "Part 3, Article 31" |
| `doc_id` | String | required | Unique ID from flattened corpus |
| `relevance_score` | Float | required, ≥0.0 | Final combined score |
| `bm25_score` | Float | default=0.0 | Raw BM25 component |
| `proximity_score` | Float | default=0.0 | Raw proximity component |
| `title_match_count` | Int | default=0 | Query term matches in title |
| `article_no` | Int | optional | |
| `clause_no` | String | optional | |
| `subclause_id` | String | optional | |
| `level` | String | optional | article/clause/subclause |
| `part_no` | Int | optional | |
| `text` | String | optional | Truncated LLM context |
| `full_text` | String | optional | Full provision text |
| `matched_terms` | List\[String\] | default=\[] | BM25 lemmatized matches |
| `exact_matched_terms` | List\[String\] | default=\[] | Exact matches for highlighting |

**Indexes**: `title`, `citation`, `doc_id`, `(title, created_at)`

### 4.3.2 Entity Relationships

```
User (1) ──── creates ────→ Message (0..*)
Message (0..*) ── references ──→ ReferencedArticle (0..*)
```

- Deleting a User deletes their Messages (CASCADE)
- Deleting a ReferencedArticle nullifies the reference in Messages

## 4.4 Authentication Design

### 4.4.1 JWT Token Structure

```python
payload = {
    'user_id': str(user.id),
    'email': user.email,
    'token_version': user.token_version,  # increments on logout
}
encoded = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
```

### 4.4.2 Token Lifecycle

1. **Login**: User authenticates → backend generates JWT with 12-hour expiry → returns in response body + sets httpOnly cookie
2. **Request**: Frontend sends token via `Authorization: Bearer` header
3. **Verification**: `@token_required` decorator decodes JWT, checks `token_version` against user document
4. **Logout**: Backend increments `user.token_version` → all previously issued JWTs become invalid

### 4.4.3 Cookie Settings

| Setting | Value |
|---------|-------|
| `httponly` | True |
| `secure` | True (production only) |
| `samesite` | Strict |
| `max_age` | 43200 (12 hours) |

The frontend stores the token in `localStorage` and sends it via the `Authorization: Bearer` header. The cookie serves as a fallback for the `@token_required` decorator.

## 4.5 Retrieval Pipeline Design

### 4.5.1 Phase 1: SearchEngine (High-Recall)

```
Query
  → BM25 Processor (lemmatize, remove stopwords) → bm25_tokens
  → Synonym Expander (44 groups) → expanded_tokens
  → Proximity Processor (raw, stopwords kept) → raw_tokens
  → Generate query pairs (all unordered if ≤5 tokens, adjacent otherwise)
  → Candidate generation (union of doc_ids from tf_index)
  → Score each candidate:
      final = BM25(k1=1.5, b=1.0) + title_boost(5.0 × title_matches) + proximity(1.0 × avg_pair_score)
  → Return top-30
```

### 4.5.2 Phase 2: Reranker (Precision + Diversity)

```
Top-30 candidates
  → Stage 2a: RRF Fusion (k=60)
    Fuse BM25 rank + proximity rank + title-match rank
  → Stage 2b: MMR Diversity (λ=0.5)
    Cosine similarity on BM25 TF vectors
  → Stage 2c: Rule-Based Boost
    score × doc.boost × part_rules[part_no] × level_rules[level]
  → Return top-8
```

### 4.5.3 Article Promotion

After reranking, clause/sub-clause results are promoted:

1. **Group** documents by `article_no`
2. Articles with their own text → use directly
3. Articles stored as individual clauses → concatenate with `\n---\n`
4. **Deduplicate** by `article_no` (highest score wins)
5. Track matched clauses for context truncation

## 4.6 API Endpoint Design

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/v1` | No | API landing page |
| GET | `/api/v1/health` | No | Liveness check |
| POST | `/api/v1/ask` | Yes | Main Q&A (JSON response) |
| POST | `/api/v1/ask-stream` | Yes | Streaming Q&A (SSE) |
| GET | `/api/v1/messages` | Yes | Paginated history |
| GET | `/api/v1/messages/<id>` | Yes | Single message |
| DELETE | `/api/v1/messages/<id>` | Yes | Delete message |
| DELETE | `/api/v1/messages` | Yes | Delete all messages |
| POST | `/api/v1/auth/register` | No | Registration |
| POST | `/api/v1/auth/login` | No | Login |
| POST | `/api/v1/auth/logout` | Yes | Logout |
| GET | `/api/v1/auth/me` | Yes | Current user info |
