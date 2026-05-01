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

- Start the API with a **full data rebuild** (flatten + index + lemma dictionary):  
  - `python app.py --rebuild-data`
- Run full offline ingestion manually:  
  - `python -m preprocessing_scripts.run_ingestion`
- Run the RAG demo script (requires Ollama):  
  - `python -m src.llm.rag_workflow`
- Regenerate the inverted index and positional index directly:  
  - `python -m preprocessing_scripts.build_index`

## Project Layout

```
app.py                          # Flask entry point, server startup, --rebuild-data flag
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
  llm/
    rag_workflow.py             # Orchestrates retrieval + optional LLM generation (Ollama)
    rag_formatter.py            # Builds prompt and context for the LLM
    ollama_llm.py               # Ollama client factory
  workflows/
    ingestion_workflow.py       # Loads flattened JSON, builds all indexes
preprocessing_scripts/          # One‑off scripts (flatten, build_index, generate_lemma_dict)
data/
  output/                       # Generated artefacts: tf_index.json, pos_index.json,
                                # doc_stats.json, lemma_dict_v3.json,
                                # flattened_nepal_constitution.json
```

## Runtime Flow (Online Q&A)

1. **Request** – `POST /api/v1/ask` with `{"query": "...", "use_llm": false/true}`
2. **Validation** – `controllers/api_controller.py` checks input
3. **Service orchestration** – `QAService` (lazy‑initialises `RAGWorkflow`)
4. **Retrieval** – `SearchEngine`:
   - **Candidate generation** – all documents containing at least one BM25 query term (lemmatised, stopwords removed)
   - **Scoring** – for each candidate, compute:
     - BM25 score (TF‑IDF based)
     - Title boost (extra weight for query tokens appearing in the article title)
     - Proximity score (minimum ordered distance between raw query term pairs, capped at 30 tokens)
   - **Combined score** = BM25 + title_boost + (proximity_weight × proximity_score)
   - **Top‑K** – sort and return the best `top_k` articles
5. **Optional LLM generation** – if `use_llm=true` and Ollama is available, `RAGWorkflow`:
   - Formats the retrieved articles as context
   - Builds a strict prompt (answer only from provided articles)
   - Calls Ollama with retries
   - Returns the generated answer alongside the retrieved citations

## Offline Ingestion Pipeline

1. **Flatten** – `flatten_constitution.py` converts the nested or flat JSON into a list of `Document` objects (article/clause/sub‑clause level)
2. **Build indexes** – `IngestionWorkflow` creates three JSON files:
   - `tf_index.json` – term → {doc_id: term frequency} (for BM25)
   - `pos_index.json` – term → {doc_id: [positions]} (for proximity scoring)
   - `doc_stats.json` – document lengths and average length (for BM25 normalisation)
3. **Lemma dictionary (optional)** – `generate_safe_lemma_dict.py` builds a rule‑based lemma map used by the `TextProcessor` when lemmatisation is enabled.

## Notes

- The server **warms up the spaCy pipeline** at startup (`preload_spacy()`) so the first request does not incur a model loading delay.
- Use `app.py --rebuild-data` to regenerate all artefacts **before** the server starts – useful after changing the source data or modifying the indexing logic.
- The retrieval engine is created once via `EngineFactory.from_artifacts()` and reused for every request.
- **Proximity scoring is only applied to BM25 candidates** (re‑ranking, not filtering). The final score combines both signals.
- If Ollama is unavailable or the requested model is missing, the API automatically falls back to retrieval‑only mode (returns only articles).
- `requirements.txt` is UTF‑16 encoded in this repository; keep that encoding unless you intentionally normalise it.
