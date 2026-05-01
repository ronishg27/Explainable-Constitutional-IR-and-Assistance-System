# services/qa_service.py
import logging
from threading import Lock

from src.core.engine_factory import EngineFactory
from src.llm.rag_workflow import RAGWorkflow

logger = logging.getLogger(__name__)

# Singleton state
_workflow = None
_workflow_lock = Lock()

# Default paths – adjust if needed
_DEFAULT_DOCS_PATH = "data/output/flattened_nepal_constitution.json"
_DEFAULT_INDEX_DIR = "data/output"


class QAService:
    """Service layer for constitution Q&A workflow orchestration."""

    @staticmethod
    def _get_workflow() -> RAGWorkflow:
        global _workflow

        if _workflow is None:
            with _workflow_lock:
                if _workflow is None:
                    # Build the engine once and inject it into RAGWorkflow
                    engine = EngineFactory.from_artifacts(
                        _DEFAULT_DOCS_PATH, _DEFAULT_INDEX_DIR
                    )
                    _workflow = RAGWorkflow(engine)
                    logger.info("RAG workflow initialised lazily on first use.")
        return _workflow

    @staticmethod
    def answer_query(query: str, useLLM: bool = False) -> tuple[dict, int]:
        """Return API response payload and HTTP status for a user query."""
        workflow = QAService._get_workflow()

        # If no LLM requested, return retrieval results only
        if not useLLM:
            retrieve_only_result = workflow.ask(query, retrieve_only=True)
            return {
                "query": query,
                "articles": retrieve_only_result.get("retrieved_articles", []),
            }, 200

        # LLM requested → check connectivity and model availability
        is_connected, status_message = workflow.check_ollama_connection()
        if not is_connected:
            logger.warning("Ollama unavailable: %s", status_message)
            return {"error": "Ollama service is unavailable."}, 503

        is_model_available, model_status, available_models = workflow.check_model_availability()
        if not is_model_available:
            logger.warning("Model unavailable: %s", model_status)
            retrieve_only_result = workflow.ask(query, retrieve_only=True)
            return {
                "query": query,
                "articles": retrieve_only_result.get("retrieved_articles", []),
                "ollama_status": {
                    "connected": True,
                    "model": workflow.model,
                    "model_available": False,
                    "message": model_status,
                    "available_models": available_models,
                },
            }, 200

        # Full RAG
        result = workflow.ask(query, stream=False, retrieve_only=False)
        return {
            "query": query,
            "response": result.get("answer"),
            "articles": result.get("retrieved_articles", []),
            "ollama_status": {
                "connected": True,
                "model": workflow.model,
                "model_available": True,
            },
        }, 200