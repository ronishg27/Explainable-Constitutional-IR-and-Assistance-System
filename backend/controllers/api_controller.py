import logging

from flask import jsonify, request

from services.qa_service import QAService

logger = logging.getLogger(__name__)


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
    useLLM = data.get("use_llm", False)

    if not query:
        return jsonify({"error": "Query is required."}), 400

    if not isinstance(query, str):
        return jsonify({"error": "Query must be a string."}), 400

    if len(query) > 500:
        return jsonify(
            {"error": "Query is too long. Maximum length is 500 characters."}
        ), 400

    try:
        payload, status_code = QAService.answer_query(query, useLLM=useLLM)
        return jsonify(payload), status_code
    except Exception as e:
        logger.exception("Error processing query")
        return jsonify({"error": "An error occurred while processing the query."}), 500
