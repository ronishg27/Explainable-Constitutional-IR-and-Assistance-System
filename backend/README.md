# Constitution Assistant Backend

Flask API and retrieval pipeline for answering questions about the Constitution of Nepal.

## Quick Start

1. Create and activate the virtual environment.  
   - PowerShell: `.venv\Scripts\Activate.ps1`
2. Install dependencies.  
   - `pip install -r requirements.txt`
3. Start the API.  
   - `python app.py`

## Common Commands

- Run full offline ingestion (flatten + index + lemma dictionary):  
  - `python -m preprocessing_scripts.run_ingestion`
- Run the RAG demo script (requires Ollama):  
  - `python -m src.llm.rag_workflow`
- Regenerate the inverted index and positional index directly:  
  - `python -m preprocessing_scripts.build_index`

## Project Layout

```
app.py                          # Flask entry point, server startup
config/                         # MongoDB connection (used for user/message persistence)
controllers/                    # Request handling, validation, auth
models/                         # MongoDB document models (User, Message, ReferencedArticle)
routes/                         # Flask blueprints (API and auth)
services/                       # Business logic (QA, User, Message, Article)
src/
  core/
    text_processor.py           # Normalisation, lemmatisation, stopwords, contractions
    index_builder.py            # Builds TF, positional, and document‑stats indexes
    bm25_scorer.py              # BM25 scoring with title boost
    proximity.py                # Proximity scoring (ordered term pairs)
    search_engine.py            # Two‑phase candidate generation + scoring
    engine_factory.py           # Assembles a SearchEngine from on‑disk artefacts
    reranker.py                 # RRF fusion + MMR diversity + rule‑based boost
  llm/
    rag_repository.py           # Retrieval + Ollama client + article promotion
    rag_workflow.py             # Orchestrates retrieval + optional LLM generation (Ollama)
    rag_formatter.py            # Builds prompt and context for the LLM
    ollama_llm.py               # Ollama client factory
  workflows/
    ingestion_workflow.py       # Loads flattened JSON, builds all indexes
    retrieval_workflow.py       # High‑recall search → rerank → top‑k
preprocessing_scripts/          # One‑off scripts (flatten, build_index, generate_lemma_dict)
data/
  output/                       # Generated artefacts: tf_index.json, pos_index.json,
                                # doc_stats.json, lemma_dict_v3.json,
                                # flattened_nepal_constitution.json
```

## Runtime Flow (Online Q&A)

1. **Request** – `POST /api/v1/ask` with `{"query": "...", "use_llm": false/true}` (requires JWT auth)
2. **Validation** – `controllers/api_controller.py` checks input and auth token
3. **Service orchestration** – `QAService` (orchestrates `RAGWorkflow` + `RAGRepository` + `RetrievalWorkflow`)
4. **Retrieval** – `RetrievalWorkflow.retrieve()`:
   - **Phase 1 (High‑recall search)** – `SearchEngine.search(query, top_k=30)`:
     - **Candidate generation** – union of all documents containing at least one BM25 query term (lemmatised, stopwords removed)
     - **Scoring** – for each candidate, compute:
       - BM25 score (TF‑IDF based)
       - Title boost (extra weight for query tokens appearing in the article title)
       - Proximity score (minimum ordered distance between raw query term pairs, capped at 30 tokens)
     - **Combined score** = BM25 + title_boost + (proximity_weight × proximity_score)
     - **Top‑30** – sort and return the best 30 candidates
   - **Phase 2 (Reranking)** – `Reranker.rerank(results, top_k=8)`:
     - RRF fusion (combines BM25 + proximity + title‑match ranks)
     - MMR diversity (cosine similarity via BM25 TF vectors)
     - Rule‑based boost (part/level multipliers)
     - Returns top 8 articles (promoted to article level)
5. **Persistence** – `_persist_message()` saves articles and query/answer to MongoDB
6. **Optional LLM generation** – if `use_llm=true` and Ollama is available, `RAGWorkflow`:
   - Formats the retrieved articles as context via `RAGFormatter`
   - Builds a strict prompt (answer only from provided articles)
   - Calls Ollama with retries via `RAGRepository.call_llm()`
   - Returns the generated answer alongside the retrieved citations

## Offline Ingestion Pipeline

1. **Flatten** – `flatten_constitution.py` converts the nested or flat JSON into a list of `Document` objects (article/clause/sub‑clause level)
2. **Build indexes** – `IngestionWorkflow` creates three JSON files:
   - `tf_index.json` – term → {doc_id: term frequency} (for BM25)
   - `pos_index.json` – term → {doc_id: [positions]} (for proximity scoring)
   - `doc_stats.json` – document lengths and average length (for BM25 normalisation)
3. **Lemma dictionary (optional)** – `generate_safe_lemma_dict.py` builds a rule‑based lemma map used by the `TextProcessor` when lemmatisation is enabled.

## Notes

- The server **warms up the spaCy pipeline** at startup so the first request does not incur a model loading delay.
- Use `python -m preprocessing_scripts.run_ingestion` to regenerate all artefacts before starting the server.
- The full retrieval pipeline is assembled eagerly at startup: `EngineFactory` → `Reranker` → `RetrievalWorkflow` → `RAGRepository` → `RAGWorkflow`.
- The default pipeline uses `recall_k=30` (from SearchEngine) + rerank to `top_k=8` (via Reranker).
- **Proximity scoring is only applied to BM25 candidates** (reranking, not filtering). The combined score feeds into RRF fusion.
- All Q&A endpoints (`/ask`, `/ask-stream`, `/messages`) require JWT authentication (`@token_required`).
- Message persistence is wired: `_persist_message()` saves articles and query/answer to MongoDB via `ArticleService` and `MessageService`.
- If Ollama is unavailable or the requested model is missing, the API automatically falls back to retrieval‑only mode (returns only articles).
- `requirements.txt` is UTF‑16 encoded in this repository; keep that encoding unless you intentionally normalise it.
