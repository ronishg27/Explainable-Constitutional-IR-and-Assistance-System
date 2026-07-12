# Constitution Assistant — API Reference

Base URL: `http://localhost:5000`

---

## Authentication

All endpoints except `register`, `login`, `/api/v1`, and `/api/v1/health` require a **JWT token** sent via:

- **Header:** `Authorization: Bearer <token>`
- **Cookie:** `token=<token>` (set automatically on login with `httpOnly`)

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
- `400` — Missing fields, short password, or duplicate email

---

### `POST /api/v1/auth/login`

Authenticate and receive a JWT (set as httpOnly cookie).

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
  "user": { "id": "...", "fullname": "John Doe", "email": "john@example.com" },
  "authenticated": true
}
```
Sets `Set-Cookie: token=<jwt>; HttpOnly; Secure; SameSite=Strict`.

**Errors:**
- `401` — Invalid credentials or user not found

---

### `POST /api/v1/auth/logout`

Clears the token cookie. Requires authentication.

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
    "/api/v1/auth/logout": "Logout the current user."
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
| `query` | `string` | — | Question text (max 500 chars) |
| `use_llm` | `bool` | `false` | If `true`, also queries the LLM for a summary answer |

**Response `200` — Retrieval-only (`use_llm: false`):**
```json
{
  "query": "What is the right to privacy?",
  "articles": [
    {
      "doc_id": "2",
      "title": "Right to privacy",
      "citation": "Article 12",
      "score": 8.5
    }
  ]
}
```

**Response `200` — With LLM (`use_llm: true`):**
```json
{
  "query": "What is the right to privacy?",
  "response": "The right to privacy is...",
  "articles": [...],
  "ollama_status": {
    "connected": true,
    "model": "gemma3:1b",
    "model_available": true
  }
}
```

**Errors:**
- `400` — Missing/empty query, query too long, invalid JSON
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
  "query": "What is the right to privacy?"
}
```

**Response `200` — SSE stream (`text/event-stream`):**

```
data: {"type": "articles", "articles": [{"doc_id": "2", "title": "Right to privacy", "citation": "Article 12", "score": 8.5}]}

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
| `error` | `content: string` | Ollama unavailable or error during generation |
| `status` | `connected`, `model`, `model_available`, `message`, `available_models` | Model not found on the server |

**Errors:**
- `400` — Missing/empty query, query too long, invalid JSON
- `401` — Missing or invalid token

> **Note:** The `answer` in the database is accumulated from all `token` events. The `articles` array in the DB records which articles were referenced.

---

### `GET /api/v1/messages`

Get paginated chat history for the authenticated user. Most recent first.

**Headers:** `Authorization: Bearer <token>`

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | `int` | `20` | Max items per page |
| `skip` | `int` | `0` | Items to skip (for pagination) |

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
          "citation": "Article 12",
          "doc_id": "2",
          "relevance_score": 8.5
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

**Errors:**
- `401` — Missing or invalid token
- `404` — User not found

---

### `GET /api/v1/messages/<message_id>`

Get a single message with its full article objects. Ownership is enforced — the message must belong to the requesting user.

**Headers:** `Authorization: Bearer <token>`

**Response `200`:**
```json
{
  "id": "6a53c2ba92e8c5db45cdce2e",
  "query": "Right to privacy?",
  "answer": "...",
  "user": { "id": "69e8da3f1d5051a808e768a3", "fullname": "John Doe", "email": "john@example.com" },
  "articles": [
    {
      "id": "6a53c25392e8c5db45cdce26",
      "title": "Right to privacy",
      "citation": "Article 12",
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

| Collection | Document |
|------------|----------|
| `users` | User accounts (name, email, password hash, role) |
| `messages` | Q&A exchanges (query, answer, user ref, article refs) |
| `referenced_articles` | Constitution articles cited in answers (deduped by `doc_id`) |
