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
- Run the RAG demo script:
  - `python src/llm/rag_workflow.py`
- Regenerate the inverted index directly:
  - `python preprocessing_scripts/build_inverted_index.py`

## Project Layout

- `app.py`: Flask entry point and server startup.
- `routes/`: request routing.
- `controllers/`: request handling and validation.
- `services/`: business logic.
- `src/core/`: text processing and ranking primitives.
- `src/llm/`: RAG workflow and Ollama integration.
- `preprocessing_scripts/`: one-off data generation scripts.
- `data/`: generated runtime artifacts.

## Notes

- `app.py --rebuild-data` rebuilds the flattened documents, inverted index, and lemma dictionary before the server starts.
- The server warms the spaCy pipeline at startup so the first request does not pay the model load cost.
- `requirements.txt` is UTF-16 encoded in this repository; keep that encoding unless you intentionally normalize it.
