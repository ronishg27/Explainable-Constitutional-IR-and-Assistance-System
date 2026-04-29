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

- Start the API with a data rebuild:
  - `python app.py --rebuild-data`
- Run full offline ingestion (flatten + index + lemma):
  - `python -m preprocessing_scripts.run_ingestion`
- Run the RAG demo script:
  - `python -m src.llm.rag_workflow`
- Regenerate the inverted index directly:
  - `python -m preprocessing_scripts.build_inverted_index`

## Project Layout

- `app.py`: Flask entry point and server startup.
- `routes/`: request routing.
- `controllers/`: request handling and validation.
- `services/`: business logic.
- `src/core/`: text processing and ranking primitives.
- `src/llm/`: RAG workflow and Ollama integration.
- `src/workflows/`: ingestion and retrieval workflow stages.
- `preprocessing_scripts/`: one-off data generation scripts.
- `data/`: generated runtime artifacts.

## Runtime Flow

1. `app.py` starts Flask and registers routes.
2. `controllers/api_controller.py` validates request input.
3. `services/qa_service.py` orchestrates the Q&A call.
4. `src/llm/rag_workflow.py` coordinates retrieval + LLM answer generation.
5. `src/workflows/ingestion_workflow.py` owns document loading/index preparation.
6. `src/workflows/retrieval_workflow.py` owns BM25 retrieval/ranking.
7. `src/llm/rag_formatter.py` builds context and prompt for the model.

## Notes

- `app.py --rebuild-data` rebuilds the flattened documents, inverted index, and lemma dictionary before the server starts.
- The server warms the spaCy pipeline at startup so the first request does not pay the model load cost.
- `requirements.txt` is UTF-16 encoded in this repository; keep that encoding unless you intentionally normalize it.
