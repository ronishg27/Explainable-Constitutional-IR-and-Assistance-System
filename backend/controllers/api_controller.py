import logging
from threading import Lock

from flask import jsonify, request

from src.llm.rag_workflow import RAGWorkflow

logger = logging.getLogger(__name__)
_workflow = None
_workflow_lock = Lock()


def get_workflow():
    global _workflow

    if _workflow is None:
        with _workflow_lock:
            if _workflow is None:
                _workflow = RAGWorkflow()
                logger.info("RAG workflow initialized lazily on first use.")

    return _workflow


def home():
    return jsonify(
        {
            "message": "Welcome to the API!",
            "endpoints": {
                "/api/v1/health": "Check the health of the API.",
                "/api/v1/ask": "Submit a query to get a response.",
                "/api/v1/auth/register": "Register a new user.",
                "/api/v1/auth/login": "Login with email and password.",
                "/api/v1/auth/logout": "Logout the current user.",
            },
            "version": "1.0.0",
        }
    )


def health():
    return jsonify({"status": "healthy"})


def ask():
    if not request.is_json:
        return jsonify({"error": "Invalid content type. Expected application/json."}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload."}), 400

    query = data.get("query")

    if not query:
        return jsonify({"error": "Query is required."}), 400

    if not isinstance(query, str):
        return jsonify({"error": "Query must be a string."}), 400

    if len(query) > 500:
        return jsonify(
            {"error": "Query is too long. Maximum length is 500 characters."}
        ), 400

    try:
        workflow = get_workflow()
        is_connected, status_message = workflow.check_ollama_connection()
        if not is_connected:
            logger.warning("Ollama unavailable during /ask: %s", status_message)
            return jsonify({"error": "Ollama service is unavailable."}), 503

        is_model_available, model_status_message, available_models = (
            workflow.check_model_availability()
        )
        if not is_model_available:
            logger.warning("Ollama model unavailable during /ask: %s", model_status_message)
            retrieve_only_result = workflow.ask(query, retrieve_only=True)
            return jsonify(
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
                }
            )

        result = workflow.ask(query, stream=False)
        return jsonify(
            {
                "query": query,
                "response": result.get("answer"),
                "articles": result.get("retrieved_articles", []),
                "ollama_status": {
                    "connected": True,
                    "model": workflow.model,
                    "model_available": True,
                },
            }
        )
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return jsonify({"error": "An error occurred while processing the query."}), 500
