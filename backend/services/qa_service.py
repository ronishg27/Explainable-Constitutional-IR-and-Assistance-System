import logging
from threading import Lock

from src.llm.rag_workflow import RAGWorkflow

logger = logging.getLogger(__name__)

_workflow = None
_workflow_lock = Lock()


class QAService:
    """Service layer for constitution Q&A workflow orchestration."""

    @staticmethod
    def _get_workflow() -> RAGWorkflow:
        global _workflow

        if _workflow is None:
            with _workflow_lock:
                if _workflow is None:
                    _workflow = RAGWorkflow()
                    logger.info("RAG workflow initialized lazily on first use.")

        return _workflow

    @staticmethod
    def answer_query(query: str, useLLM: bool = False) -> tuple[dict, int]:
        """Return API response payload and HTTP status for a user query."""
        workflow = QAService._get_workflow()

        # If not using LLM, skip Ollama checks and return retrieval-only results
        if not useLLM:
            retrieve_only_result = workflow.ask(query, retrieve_only=True)
            return (
                {
                    "query": query,
                    "articles": retrieve_only_result.get("retrieved_articles", []),
                },
                200,
            )

        # Only check Ollama when LLM is requested
        is_connected, status_message = workflow.check_ollama_connection()
        if not is_connected:
            logger.warning("Ollama unavailable during /ask: %s", status_message)
            return {"error": "Ollama service is unavailable."}, 503

        is_model_available, model_status_message, available_models = (
            workflow.check_model_availability()
        )
        if not is_model_available:
            logger.warning("Ollama model unavailable during /ask: %s", model_status_message)
            retrieve_only_result = workflow.ask(query, retrieve_only=True)
            return (
                {
                    "query": query,
                    "articles": retrieve_only_result.get("retrieved_articles", []),
                    "ollama_status": {
                        "connected": True,
                        "model": workflow.model,
                        "model_available": False,
                        "message": model_status_message,
                        "available_models": available_models,
                    },
                },
                200,
            )

        result = workflow.ask(query, stream=False, retrieve_only=False)
        return (
            {
                "query": query,
                "response": result.get("answer"),
                "articles": result.get("retrieved_articles", []),
                "ollama_status": {
                    "connected": True,
                    "model": workflow.model,
                    "model_available": True,
                },
            },
            200,
        )
