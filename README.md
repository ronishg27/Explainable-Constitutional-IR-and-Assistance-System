# Constitution Assistant

**Explainable Constitutional IR and Assistance System** — a Retrieval-Augmented Generation (RAG) system that answers natural-language questions about the **Constitution of Nepal (2072 / 2015)**.

Users ask legal questions in plain English and receive ranked constitutional provisions from a custom hybrid search engine, optionally with an LLM-grounded answer.

## Features

- **Hybrid Legal Search** — BM25 + term proximity + title boost tuned for legal text
- **Synonym Expansion** — 44 legal synonym groups for improved recall
- **Multi-stage Reranking** — RRF fusion + MMR diversity + rule-based boost
- **RAG (Retrieval-Augmented Generation)** — Ollama-powered answers grounded strictly in retrieved articles
- **Streaming Responses** — SSE-based real-time token delivery
- **User Authentication** — JWT-based registration/login/logout with token version invalidation
- **Chat History** — Full CRUD with pagination and ownership enforcement
- **Graceful Degradation** — Falls back to retrieval-only if Ollama is unavailable

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Frontend (React 19 + Vite 8)                  │
│  Pages: Home, Login, Register, History, About, HowItWorks       │
│  Streaming: SSE via ReadableStream.getReader()                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ POST /api/v1/ask (JWT Bearer auth)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (Flask / Python 3.13)               │
│  Routes (Blueprints) → Controllers → Services                   │
│    ↓                                                            │
│  IR Engine (BM25 + Proximity + RRF/MMR Reranker)                │
│  RAG Layer (Retrieval + Prompt Formatting + Ollama Client)      │
└────────────┬──────────────────────────────────┬─────────────────┘
             │                                  │
        MongoDB 8                          Ollama (optional)
    (Users, Messages, Articles)         (qwen3:8b default)
```

## Quick Start

### Prerequisites

- Python 3.13
- MongoDB 8 (running locally or remote)
- Node.js 22
- Ollama (optional — system works without it)
- Copy `backend/.env.sample` → `backend/.env` and configure MongoDB URI / JWT secret

### Run both apps

```powershell
make run
```

This starts the backend (Flask on `http://localhost:5000`) and frontend (Vite dev server on `http://localhost:5173`).

### Makefile targets

| Target     | Command              | Description                                       |
| ---------- | -------------------- | ------------------------------------------------- |
| `run`      | `make` or `make run` | Launch backend + frontend in separate cmd windows |
| `backend`  | `make backend`       | Start Flask API only (port 5000)                  |
| `frontend` | `make frontend`      | Start Vite dev server only (port 5173)            |

### Manual start

**Backend:**

```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

**Frontend:**

```powershell
cd frontend
npm install
npm run dev
```

**Ingestion (first time or after data change):**

```powershell
cd backend
python -m preprocessing_scripts.run_ingestion
```

## Project Structure

```
backend/               Flask API + custom IR engine
  app.py               Server entry point
  controllers/         Request handling and validation
  routes/              Flask blueprints
  services/            Business logic (QA, User, Message, Article)
  src/
    core/              BM25, proximity, search, reranker, text processing
    llm/               RAG workflow, formatter, Ollama client
    workflows/         Ingestion and retrieval workflows
  preprocessing_scripts/  Flatten JSON → build indexes
  data/output/         Generated index artefacts
  config/              MongoDB connection
  models/              ODM models (User, Message, ReferencedArticle)

frontend/              React 19 SPA
  src/pages/           Route-level page components
  src/components/      Shared UI components
  src/hooks/           Auth context, streaming hook

docs/                  Architecture, API docs, algorithm details, FYP report
```

## Tech Stack

| Layer    | Technology                                        |
| -------- | ------------------------------------------------- |
| Backend  | Flask, spaCy, custom BM25/MMR IR engine           |
| Frontend | React 19, Vite 8, Tailwind CSS v4, React Router 7 |
| Database | MongoDB 8                                         |
| LLM      | Ollama (qwen3:8b) — optional                      |

## Documentation

- [System Overview](docs/SYSTEM_OVERVIEW.md)
- [Project Documentation](docs/PROJECT_DOCUMENTATION.md)
- [API Documentation](docs/api_docs.md)
- [Algorithm Details](docs/algorithm_details.md)
- [Repository Tour](docs/REPOSITORY_TOUR.md)
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)

## Authors

Ronish Ghimire, Devraj Khatiwada, Nayan Nepal

## License

MIT
