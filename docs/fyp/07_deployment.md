# Chapter 7: Deployment and User Manual

## 7.1 System Requirements

### 7.1.1 Hardware Requirements
- **CPU**: x86-64, 2+ cores recommended
- **RAM**: 4 GB minimum (8 GB recommended if running Ollama)
- **Storage**: 500 MB for application + indexes (additional space for Ollama models ~4 GB)
- **Network**: Localhost only (no external network required after installation)

### 7.1.2 Software Requirements
- **Python**: 3.13+
- **Node.js**: 22+
- **MongoDB**: 8.0+ (local installation required)
- **Ollama**: Optional, for LLM features

## 7.2 Installation Guide

### 7.2.1 Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Note: requirements.txt is UTF-16 encoded.
# If pip fails, save a UTF-8 copy before installing.

# Configure environment
cp .env.sample .env
# Edit .env with your values (at minimum, set JWT_SECRET)
```

**Environment Variables** (`backend/.env`):

| Variable | Default | Required | Description |
|----------|---------|:--------:|-------------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | No | Ollama server URL |
| `OLLAMA_API_KEY` | (empty) | No | Bearer token for Ollama |
| `OLLAMA_MODEL` | `qwen3:8b` | No | LLM model name |
| `MONGO_URI` | `mongodb://localhost:27017` | No | MongoDB connection string |
| `MONGO_DB_NAME` | `ECIRAS` | No | Database name |
| `JWT_SECRET` | (must set) | Yes | HS256 signing key |

### 7.2.2 Database Setup

Ensure MongoDB is running on `localhost:27017`:

```powershell
# Start MongoDB (example for local installation)
mongod --dbpath "C:\data\db"
```

The system uses database `ECIRAS` and creates collections `users`, `messages`, and `referenced_articles` automatically on first use.

### 7.2.3 Build Indexes (First Time)

```powershell
# From backend directory with venv activated
python -m preprocessing_scripts.run_ingestion
```

This runs the complete ingestion pipeline:
1. Flattens `data/nepal_constitution_new.json` → `data/output/flattened_nepal_constitution.json`
2. Builds `tf_index.json`, `pos_index.json`, `doc_stats.json`

### 7.2.4 Frontend Setup

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend starts on `http://localhost:5173`.

### 7.2.5 Optional: Ollama Setup

```powershell
# Start Ollama server
ollama serve

# Pull the default model
ollama pull qwen3:8b
```

## 7.3 Running the System

### 7.3.1 Start All Services

**Terminal 1 — Backend:**
```powershell
cd backend
.venv\Scripts\Activate.ps1
python app.py
# Server starts on http://127.0.0.1:5000
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
# Dev server starts on http://localhost:5173
```

**Terminal 3 — MongoDB (if not running as a service):**
```powershell
mongod
```

**Terminal 4 — Ollama (optional):**
```powershell
ollama serve
```

### 7.3.2 Using the Makefile

From the project root:
```powershell
make backend    # Start backend server
make frontend   # Start frontend dev server
make run        # Start both in separate windows
```

## 7.4 User Manual

### 7.4.1 Registration

1. Navigate to `http://localhost:5173/register`
2. Enter your fullname, email, and password (minimum 6 characters)
3. Click "Register" — you will be redirected to the login page

### 7.4.2 Login

1. Navigate to `http://localhost:5173/login`
2. Enter your email and password
3. Click "Login" — you will be redirected to the home page

### 7.4.3 Asking a Question

1. On the home page, type your question in the search bar (e.g., "What is the right to education?")
2. Toggle "Use AI" to enable/disable LLM-generated answers
3. Click "Search" or press Enter
4. The system retrieves relevant articles displayed as expandable cards on the right
5. If AI is enabled, a streamed answer appears on the left

**Suggestion Pills:** Click any of the 6 preset questions for quick access:
- "How is the President of Nepal elected?"
- "What fundamental rights are guaranteed to citizens?"
- "How can a person acquire citizenship of Nepal?"
- "What are the duties and obligations of the State?"
- "What is the structure of the Federal Parliament?"
- "What rights do senior citizens have under the constitution?"

### 7.4.4 Understanding Results

Each article card shows:
- **Rank badge**: Position in results
- **Title and citation**: e.g., "Right relating to education — Part 3, Article 31"
- **Confidence badge**: High (≥70%), Medium (≥40%), or Low (<40%)
- **Matched terms**: Tags showing which query terms matched
- **Score breakdown** (expanded): BM25 score, proximity score, title boost, and boost multiplier

Click on a card to expand it and see the full text with highlighted terms.

### 7.4.5 Viewing Chat History

1. Click "History" in the navigation bar
2. Browse past Q&A sessions (paginated, 20 per page)
3. Click a session to view the full details
4. Use the delete button to remove individual messages
5. Use "Clear All" to remove all messages

### 7.4.6 Logout

Click "Logout" in the navigation bar. This invalidates your session token.

## 7.5 API Usage Examples

### Health Check
```bash
curl http://localhost:5000/api/v1/health
```
Response: `{"status": "healthy"}`

### Registration
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"fullname": "Test User", "email": "test@example.com", "password": "pass123"}'
```

### Login
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "pass123"}'
```

### Submit Query (Retrieval Only)
```bash
curl -X POST http://localhost:5000/api/v1/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "Right to education", "use_llm": false}'
```

### Submit Query (RAG)
```bash
curl -X POST http://localhost:5000/api/v1/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "What is the right to education?", "use_llm": true}'
```

### Get Chat History
```bash
curl http://localhost:5000/api/v1/messages?limit=10&skip=0 \
  -H "Authorization: Bearer <token>"
```

## 7.6 File Index Artifacts

All generated in `backend/data/output/`:

| File | Purpose | Generated By |
|------|---------|-------------|
| `flattened_nepal_constitution.json` | ~700 flat documents (articles, clauses, sub-clauses) | `flatten_constitution.py` |
| `tf_index.json` | Term → {doc_id: term frequency} for BM25 | `build_index.py` |
| `pos_index.json` | Term → {doc_id: [positions]} for proximity | `build_index.py` |
| `doc_stats.json` | Document lengths + average document length | `build_index.py` |

## 7.7 Useful Commands

```powershell
# Backend
python app.py                          # Start server
python -m preprocessing_scripts.run_ingestion  # Full pipeline (flatten → index → lemma)
python -m preprocessing_scripts.build_index     # Indexes only
python -m src.llm.rag_workflow         # CLI RAG demo
pytest backend/temp/tests/             # Run tests

# Frontend
npm run dev                            # Dev server (HMR)
npm run build                          # Production build
npm run lint                           # ESLint check
npm run preview                        # Preview production build
```
