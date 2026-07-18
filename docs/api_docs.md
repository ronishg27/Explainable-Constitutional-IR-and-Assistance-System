# Constitution Assistant — API Reference

Base URL: `http://localhost:5000`

---

## Authentication

All endpoints except `register`, `login`, `/api/v1`, and `/api/v1/health` require a **JWT token**.

**How to send the token:**
- **Bearer header (primary, used by frontend):** `Authorization: Bearer <token>`
- **Cookie (set by backend on login):** `token=<token>` (httpOnly, SameSite=Strict, Secure in production)

**Token storage (frontend):** The React app stores the JWT in `localStorage` and sends it via the `Authorization: Bearer` header. The backend sets both a cookie (for fallback) and returns the token in the login response body.

---

## Auth Endpoints

### `POST /api/v1/auth/register`

Create a new user account.

**Request:**
```json
{
  "fullname": "John Doe",
  "email": "john@example.com",
  "password": "supersecret123"
}
```

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `fullname` | string | yes | 3–50 characters |
| `email` | string | yes | Must be valid email format |
| `password` | string | yes | Minimum 6 characters |
| `role` | string | no | `"user"` or `"admin"` (default `"user"`) |

**Response `201` — Created:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": "66a1b2c3d4e5f67890123456",
    "fullname": "John Doe",
    "email": "john@example.com",
    "created_at": "2026-07-12T00:00:00",
    "updated_at": "2026-07-12T00:00:00"
  }
}
```

**Errors:**
- `400` — Missing fields, invalid email, short password, duplicate email, invalid role

---

### `POST /api/v1/auth/login`

Authenticate and receive a JWT (returned in body + set as httpOnly cookie).

**Request:**
```json
{
  "email": "john@example.com",
  "password": "supersecret123"
}
```

**Response `200` — Success:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "66a1b2c3d4e5f67890123456",
    "fullname": "John Doe",
    "email": "john@example.com"
  },
  "authenticated": true,
  "token": "<jwt-string>"
}
```

Also sets `Set-Cookie: token=<jwt>; HttpOnly; SameSite=Strict; Max-Age=43200` (12h). `Secure` flag is only set in production.

**Errors:**
- `401` — Invalid credentials or user not found

---

### `POST /api/v1/auth/logout`

Invalidates the current JWT (increments `token_version` on the user) and clears the cookie. Requires authentication.

**Headers:** `Authorization: Bearer <token>`

**Response `200`:**
```json
{ "message": "Logout successful." }
```

---

### `GET /api/v1/auth/me`

Get the currently authenticated user's profile.

**Headers:** `Authorization: Bearer <token>`

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "id": "66a1b2c3d4e5f67890123456",
    "fullname": "John Doe",
    "email": "john@example.com",
    "created_at": "2026-07-12T00:00:00",
    "updated_at": "2026-07-12T00:00:00"
  },
  "message": "User retrieved successfully"
}
```

**Errors:**
- `401` — Missing or invalid token
- `404` — User not found

---

## API Endpoints

### `GET /api/v1`

List all available endpoints.

**Response `200`:**
```json
{
  "message": "Welcome to the API!",
  "endpoints": {
    "/api/v1/health": "Check the health of the API.",
    "/api/v1/ask": "Submit a query to get a response.",
    "/api/v1/ask-stream": "Submit a query and stream the response.",
    "/api/v1/auth/register": "Register a new user.",
    "/api/v1/auth/login": "Login with email and password.",
    "/api/v1/auth/logout": "Logout the current user.",
    "/api/v1/auth/me": "Get the current logged in user.",
    "/api/v1/messages": "List or delete chat history.",
    "/api/v1/messages/<id>": "Get or delete a specific message."
  },
  "version": "1.0.0"
}
```

---

### `GET /api/v1/health`

Simple health check.

**Response `200`:**
```json
{ "status": "healthy" }
```

---

### `POST /api/v1/ask`

Submit a question and get a JSON response with retrieved articles and (optionally) an LLM-generated answer.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "query": "What is the right to privacy?",
  "use_llm": false
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | — | Question text (max 500 chars) |
| `use_llm` | bool | `false` | If `true`, also queries the LLM for a summary answer |

**Response `200` — Retrieval-only (`use_llm: false`):**
```json
{
  "query": "What is the right to privacy?",
  "articles": [
    {
      "doc_id": "2",
      "part_no": "3",
      "article_no": 12,
      "title": "Right to privacy",
      "text": "...",
      "citation": "Part 3, Article 12",
      "level": "article",
      "clause_no": null,
      "subclause_id": null,
      "score": 8.5,
      "bm25_score": 6.2,
      "proximity_score": 2.3,
      "title_match_count": 1,
      "matched_terms": ["right", "privacy"],
      "exact_matched_terms": ["right", "privacy"],
      "boost_multiplier": 0.98
    }
  ]
}
```

**Response `200` — With LLM (`use_llm: true`):**
```json
{
  "query": "What is the right to privacy?",
  "response": "The right to privacy is guaranteed under Article 12...",
  "articles": [
    {
      "doc_id": "2",
      "part_no": "3",
      "article_no": 12,
      "title": "Right to privacy",
      "text": "...",
      "citation": "Part 3, Article 12",
      "level": "article",
      "clause_no": null,
      "subclause_id": null,
      "score": 8.5,
      "bm25_score": 6.2,
      "proximity_score": 2.3,
      "title_match_count": 1,
      "matched_terms": ["right", "privacy"],
      "exact_matched_terms": ["right", "privacy"],
      "boost_multiplier": 0.98
    }
  ],
  "ollama_status": {
    "connected": true,
    "model": "qwen3:8b",
    "model_available": true
  }
}
```

**Response `200` — Model missing (retrieval-only fallback):**
```json
{
  "query": "What is the right to privacy?",
  "articles": [...],
  "ollama_status": {
    "connected": true,
    "model": "qwen3:8b",
    "model_available": false,
    "message": "Model 'qwen3:8b' is unavailable.",
    "available_models": ["llama3.2:3b", "nomic-embed-text"]
  }
}
```

**Behavior Matrix:**

| `use_llm` | Ollama State | HTTP Status | Response Includes |
|:---------:|--------------|:-----------:|-------------------|
| `false` | — | 200 | `query` + `articles` |
| `true` | Connected, model loaded | 200 | `query` + `articles` + `response` + `ollama_status` (all available) |
| `true` | Connected, model missing | 200 | `query` + `articles` + `ollama_status` (model_available=false) |
| `true` | Unreachable | 503 | `error`: "Ollama service is unavailable." |
| `true` | LLM call fails after 3 retries | 200 | `query` + `articles` + `response` (error text) + `error` field |

**Errors:**
- `400` — Missing/empty query, query too long, invalid JSON, wrong content type
- `401` — Missing or invalid token
- `503` — Ollama service unavailable (when `use_llm: true`)

---

### `POST /api/v1/ask-stream`

Submit a question and receive a **Server-Sent Events (SSE)** stream. Each event is a JSON line prefixed with `data: ` and separated by `\n\n`.

**Headers:** `Authorization: Bearer <token>`
**Content-Type:** `application/json`

**Request:**
```json
{
  "query": "What is the right to privacy?",
  "use_llm": true
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | — | Question text (max 500 chars) |
| `use_llm` | bool | `true` | If `false`, only retrieves articles (no LLM) |

**Response `200` — SSE stream (`text/event-stream`):**

```
data: {"type": "articles", "articles": [{"doc_id": "2", "title": "Right to privacy", ...}]}

data: {"type": "token", "content": "The right to privacy is "}

data: {"type": "token", "content": "guaranteed under Article 12"}

data: {"type": "done"}
```

**Event types:**

| Type | Fields | When |
|------|--------|------|
| `articles` | `articles: [...]` | Immediately — retrieved documents |
| `token` | `content: string` | Each partial LLM response chunk |
| `done` | *(none)* | Stream complete |
| `error` | `content: string` | Ollama unavailable or generation error (no more events follow) |
| `status` | `connected`, `model`, `model_available`, `message`, `available_models` | Model not found on the server |

**Notes:**
- The `articles` event is always the first event (unless `use_llm=false`, in which case it's followed immediately by `done`)
- The frontend accumulates all `token` events into the full answer
- The persisted answer in MongoDB is the concatenation of all token events
- The `use_llm` field defaults to `true` on this endpoint (vs `false` on `/ask`)

---

### `GET /api/v1/messages`

Get paginated chat history for the authenticated user. Most recent first.

**Headers:** `Authorization: Bearer <token>`

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | `20` | Max items per page |
| `skip` | int | `0` | Items to skip (for pagination) |

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "id": "6a53c2ba92e8c5db45cdce2e",
      "query": "Right to privacy?",
      "answer": "The right to privacy is...",
      "user": {
        "id": "69e8da3f1d5051a808e768a3",
        "fullname": "John Doe",
        "email": "john@example.com"
      },
      "articles": [
        {
          "id": "6a53c25392e8c5db45cdce26",
          "title": "Right to privacy",
          "citation": "Part 3, Article 12",
          "doc_id": "2",
          "relevance_score": 8.5,
          "bm25_score": 6.2,
          "proximity_score": 2.3,
          "article_no": 12,
          "clause_no": null,
          "level": "article",
          "matched_terms": ["right", "privacy"]
        }
      ],
      "created_at": "2026-07-12T16:37:14.087000",
      "updated_at": "2026-07-12T16:37:14.087000"
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 20,
    "skip": 0,
    "has_more": false
  }
}
```

---

### `GET /api/v1/messages/<message_id>`

Get a single message with its full article objects. Ownership is enforced.

**Headers:** `Authorization: Bearer <token>`

**Response `200`:**
```json
{
  "id": "6a53c2ba92e8c5db45cdce2e",
  "query": "Right to privacy?",
  "answer": "...",
  "user": {
    "id": "69e8da3f1d5051a808e768a3",
    "fullname": "John Doe",
    "email": "john@example.com"
  },
  "articles": [
    {
      "id": "6a53c25392e8c5db45cdce26",
      "title": "Right to privacy",
      "citation": "Part 3, Article 12",
      "doc_id": "2",
      "relevance_score": 8.5
    }
  ],
  "created_at": "2026-07-12T16:37:14.087000",
  "updated_at": "2026-07-12T16:37:14.087000"
}
```

**Errors:**
- `401` — Missing or invalid token
- `403` — Forbidden (message belongs to another user)
- `404` — Message not found

---

### `DELETE /api/v1/messages/<message_id>`

Delete a single chat message. Only the owner can delete their own messages.

**Headers:** `Authorization: Bearer <token>`

**Response `200`:**
```json
{
  "success": true,
  "message": "Message deleted successfully"
}
```

---

### `DELETE /api/v1/messages`

Delete **all** chat messages for the authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response `200`:**
```json
{
  "success": true,
  "message": "5 messages deleted successfully"
}
```

---

## Error Response Format

All error responses follow this shape:

```json
{
  "error": "Human-readable error description"
}
```

| Status | Meaning |
|--------|---------|
| `400` | Bad request (invalid payload, missing fields, validation) |
| `401` | Unauthorized (missing/expired/invalid token) |
| `403` | Forbidden (resource doesn't belong to the user) |
| `404` | Resource not found |
| `500` | Internal server error |
| `503` | Ollama service unavailable |

---

## Database Collections

| Collection | Document | Purpose |
|------------|----------|---------|
| `users` | User | Accounts (name, email, bcrypt hash, role, token_version) |
| `messages` | Message | Q&A history (query, answer, user ref, article refs) |
| `referenced_articles` | ReferencedArticle | Constitution articles cited in answers (deduplicated by `doc_id`, with full scoring metadata) |
