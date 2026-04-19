# Explainable Constitutional IR and Assistance System - Project Documentation

**Project Name:** Explainable Constitutional IR and Assistance System  
**Version:** 2.0.0 (documentation refresh)  
**Last Updated:** April 19, 2026  
**Purpose:** Retrieval-Augmented constitutional question answering for Nepal's Constitution, combining BM25 search with LLM-based response generation.  
**Author:** Ronish Ghimire, Devraj Khatiwada, Nayan Nepal

---

## 1. Project Overview

### What the System Does
This project is a constitutional assistant API that accepts natural language questions and returns:
- A generated answer from an LLM
- Retrieved constitutional references used as evidence
- Ranked citations based on lexical relevance (BM25 with title boosting)

The current implementation is **RAG-first** (retrieval + generation), not retrieval-only.

### Core User Flow
1. User sends a question to `POST /api/v1/ask`
2. Backend retrieves top constitutional passages using BM25
3. Retrieved passages are formatted into context
4. Ollama model generates a grounded answer from that context
5. API returns answer + retrieved article metadata

### Primary Technologies
- **Backend:** Flask 3.x
- **Cross-origin support:** flask-cors
- **Env management:** python-dotenv
- **Retrieval:** BM25 (custom implementation)
- **Generation:** Ollama client (`ollama` Python package)
- **Data format:** JSON corpus + JSON metadata

---

## 2. Current Architecture (Actual)

```
Client (Postman / UI)
        |
        v
Flask API (backend/app.py)
  - GET /api/v1
  - GET /api/v1/health
  - POST /api/v1/ask
        |
        v
RAGWorkflow (backend/src/llm/rag_workflow.py)
  |- load_documents(...flattened_nepal_constitution.json)
  |- BM25 index build (backend/src/core/bm25.py)
  |- retrieve top-k with title boost
  |- build prompt with retrieved constitutional context
  |- call Ollama chat model
        |
        v
Response JSON
  - query
  - response (LLM answer)
  - articles (retrieved evidence docs)
```

### Important Reality Check
The API endpoint is **already integrated** with retrieval and generation logic. It is no longer a placeholder-only route.

---

## 3. Repository Structure Snapshot

```
backend/
  app.py
  requirements.txt
  bm25.py
  boolean_search.py
  ii_tf.py
  text_processing.py
  demo_rag.py
  data/
    Constitution-of-Nepal_2072.pdf
    flattened_nepal_constitution.json
    inverted_index_mvp.json
    nepal_constitution_mvp.json
  preprocessing_scripts/
    build_inverted_index_mvp.py
    filter_lemma_dict.py
    flatten_articles.py
    flatten_mvp_constitution.py
    generate_safe_lemma_dict.py
  src/
    constants/
      stopwords.py
    core/
      bm25.py
      preprocessing.py
    llm/
      ollama_llm.py
      rag_workflow.py

postman/
  collections/
  environments/

frontend/
  .gitkeep
```

### Notes
- The active runtime path for API retrieval is `backend/src/core/bm25.py` via `backend/src/llm/rag_workflow.py`.
- `frontend/` currently contains no application implementation.
- There are duplicate/legacy retrieval modules in root `backend/` that are useful for experimentation but are not the main API path.

---

## 4. API Interface (Implemented)

## Base URL
`http://localhost:5000/api/v1`

## Endpoint: Home
- **Method:** `GET`
- **Path:** `/api/v1`
- **Purpose:** API landing metadata

## Endpoint: Health
- **Method:** `GET`
- **Path:** `/api/v1/health`
- **Purpose:** Basic liveliness check

## Endpoint: Ask (Main)
- **Method:** `POST`
- **Path:** `/api/v1/ask`
- **Request body:**
```json
{
  "query": "Discuss the concept of sovereignty and state power in Nepal."
}
```

- **Success response shape (current):**
```json
{
  "query": "...",
  "response": "LLM answer text...",
  "articles": [
    {
      "doc_id": "...",
      "article_no": 1,
      "title": "...",
      "citation": "Part X, Article Y...",
      "score": 12.34
    }
  ]
}
```

- **Current failure behavior:**
  - If Ollama connection fails, returns `500` with `{"error": "Failed to connect to Ollama."}`

---

## 5. Retrieval and Ranking Logic

### Active BM25 Engine
Implemented in `backend/src/core/bm25.py`:
- Default params: `k1=1.5`, `b=0.75`
- Uses pre-tokenized `body_tokens` when available, else tokenizes text
- Computes IDF with BM25 standard variant
- Supports title boosting through `score_with_boost(...)`

### Query Preprocessing
Runtime preprocessing is done through `NLP.tokenize(...)` from `backend/src/core/preprocessing.py`.
- Lowercasing and punctuation normalization
- Stopword filtering using `backend/src/constants/stopwords.py`

### Title Boosting
Final ranking score is:
- BM25 body score
- Plus `title_boost * overlap(query_tokens, title_tokens)`

Default `title_boost` currently used in workflow: `5.0`.

---

## 6. RAG Workflow Details

Implemented in `backend/src/llm/rag_workflow.py`.

### Steps
1. Load constitution corpus from `backend/data/flattened_nepal_constitution.json`
2. Build BM25 index in memory
3. Retrieve top-k relevant documents (`max_context_articles`, default `5`)
4. Format retrieved passages into a structured constitutional context
5. Build instruction prompt constrained to provided articles
6. Call Ollama chat model (default: `llama2:7b-chat`)
7. Return answer and citations

### Model Options in Code
Enum includes:
- `llama2:7b-chat`
- `qwen3:4b`
- `qwen3:8b`
- `gemma3:1b`
- `glm-5:cloud`

### Ollama Client Setup
In `backend/src/llm/ollama_llm.py`:
- `OLLAMA_HOST` env var supported (default `http://127.0.0.1:11434`)
- Optional bearer token from `OLLAMA_API_KEY`

---

## 7. Data Pipeline and Assets

### Canonical Data Files (current)
- `backend/data/nepal_constitution_mvp.json` (structured source)
- `backend/data/flattened_nepal_constitution.json` (main retrieval corpus)
- `backend/data/inverted_index_mvp.json` (prebuilt lexical index)
- `backend/data/Constitution-of-Nepal_2072.pdf` (source reference)

### Preprocessing Scripts
- `flatten_mvp_constitution.py`: creates normalized flat docs (article/clause/sub-clause levels)
- `build_inverted_index_mvp.py`: builds token -> document-frequency postings
- `flatten_articles.py`: alternate flattening utility for different input schema variants
- `filter_lemma_dict.py`, `generate_safe_lemma_dict.py`: lemma-related utilities

### Output Document Schema (flattened corpus)
Typical fields include:
- `doc_id`
- `part_no`
- `article_no`
- `clause_no`
- `subclause_id`
- `level`
- `title`
- `text`
- `citation`
- `title_tokens`
- `body_tokens`

---

## 8. Implementation Status (Accurate as of April 2026)

### Implemented
- Flask API routes (`/api/v1`, `/api/v1/health`, `/api/v1/ask`)
- BM25 retrieval with title boosting
- RAG orchestration (retrieve + prompt + LLM answer)
- Ollama connectivity check before answering
- Postman collection and environment for quick API testing

### Partially Implemented / In Progress
- Better runtime efficiency (index/workflow currently rebuilt per request)
- Unified preprocessing stack across all modules (duplicate utilities still exist)
- Stronger request validation and robust error handling

### Not Yet Implemented
- Fully built frontend experience
- Automated test suite (unit/integration coverage)
- Production-grade observability (structured logs/metrics/traces)
- Multi-language query support (e.g., Nepali)

---

## 9. Known Issues and Technical Debt

1. **Per-request initialization overhead**
- `RAGWorkflow()` is created inside each `/ask` request.
- This reloads documents and rebuilds BM25 repeatedly.

2. **Input validation gaps**
- `query` field currently has limited validation (empty/malformed body handling is minimal).

3. **Preprocessing duplication**
- Multiple tokenizer/search implementations exist (`backend/bm25.py`, `backend/ii_tf.py`, `backend/src/core/bm25.py`).
- This increases maintenance burden and risks inconsistent behavior.

4. **Lemmatization path is inconsistent**
- Lemma scripts exist, but active runtime path is mostly tokenization + stopword removal.

5. **requirements.txt encoding caution**
- File appears to be UTF-16 encoded; tools assuming UTF-8 may misread it.

---

## 10. Recommendations for Project Report and Next Milestone

### A. Immediate (High Priority)
1. Move `RAGWorkflow` initialization to app startup (singleton/service-level cache).
2. Add request validation for `/ask`:
   - missing JSON
   - missing/empty `query`
   - max query length
3. Improve error messages for model/data failures.

### B. Short Term
1. Consolidate retrieval code into one canonical module (`backend/src/core`).
2. Add logging for retrieval latency, generation latency, and failure reason.
3. Add unit tests for preprocessing and BM25 scoring.

### C. Medium Term
1. Add retrieval-only mode in API for explainability/debugging.
2. Add answer grounding signals (which context chunks influenced the answer).
3. Add Nepali language support path and query normalization strategy.

---

## 11. Report-Ready Summary

This project currently functions as a **Retrieval-Augmented Constitutional Assistant** rather than a plain IR prototype. The backend retrieves relevant constitutional provisions using BM25 with title boosting, then uses an Ollama-hosted model to generate concise, citation-aware answers. The architecture is practical and operational for demos and academic evaluation, with clear improvement opportunities in validation, performance optimization, and code consolidation.

---

## Appendix: Quick Run Checklist

1. Create and activate virtual environment in `backend/`
2. Install dependencies from `backend/requirements.txt`
3. Ensure Ollama is running (`ollama serve`) and model is available locally
4. Start API (`python app.py`)
5. Test:
   - `GET /api/v1`
   - `GET /api/v1/health`
   - `POST /api/v1/ask`
