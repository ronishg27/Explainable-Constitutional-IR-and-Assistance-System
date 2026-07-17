import json
import logging
import time
from typing import Generator

from flask import Response, jsonify, request, stream_with_context

from services.message_service import MessageService
from services.qa_service import QAService

logger = logging.getLogger(__name__)


def home() -> Response:
    """GET /api/v1/ — list available endpoints."""
    return jsonify(
        {
            "message": "Welcome to the API!",
            "endpoints": {
                "/api/v1/health": "Check the health of the API.",
                "/api/v1/ask": "Submit a query to get a response.",
                "/api/v1/ask-stream": "Submit a query and stream the response.",
                "/api/v1/auth/register": "Register a new user.",
                "/api/v1/auth/login": "Login with email and password.",
                "/api/v1/auth/logout": "Logout the current user.",
                "/api/v1/auth/me": "Get the current logged in user.",
                "/api/v1/messages": "List or delete chat history.",
                "/api/v1/messages/<id>": "Get or delete a specific message.",
            },
            "version": "1.0.0",
        }
    )


def health() -> Response:
    """GET /api/v1/health — readiness check."""
    return jsonify({"status": "healthy"})


def ask() -> Response:
    """POST /api/v1/ask — answer a question (synchronous)."""
    start = time.time()
    if not request.is_json:
        return jsonify({"error": "Invalid content type. Expected application/json."}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload."}), 400

    query = data.get("query")
    use_llm = data.get("use_llm", False)

    if not query:
        return jsonify({"error": "Query is required."}), 400

    if not isinstance(query, str):
        return jsonify({"error": "Query must be a string."}), 400

    if len(query) > 500:
        return jsonify(
            {"error": "Query is too long. Maximum length is 500 characters."}
        ), 400

    try:
        payload, status_code = QAService.answer_query(query, use_llm=use_llm)

        if status_code == 200:
            user_id = request.user.get("user_id")
            QAService.persist_message(user_id, query, payload)

        elapsed = time.time() - start
        logger.info(
            "query=%s use_llm=%s status=%d latency=%.2fs",
            query[:80], use_llm, status_code, elapsed,
        )
        return jsonify(payload), status_code
    except Exception:
        logger.exception("Error processing query")
        return jsonify({"error": "An error occurred while processing the query."}), 500


def _stream_events(user_id: str, query: str, use_llm: bool, events) -> Generator[str, None, None]:
    """Consume QAService events, persist on done, yield SSE lines."""
    stream_start = time.time()
    full_answer = ""
    articles_data = []

    for event in events:
        if event["type"] == "articles":
            articles_data = event.get("articles", [])
        elif event["type"] == "token":
            full_answer += event.get("content", "")
        elif event["type"] == "done":
            payload = {
                "articles": articles_data,
                "response": full_answer,
            }
            QAService.persist_message(user_id, query, payload)
            elapsed = time.time() - stream_start
            logger.info(
                "stream query=%s use_llm=%s latency=%.2fs",
                query[:80], use_llm, elapsed,
            )

        yield f"data: {json.dumps(event)}\n\n"


def ask_stream() -> Response:
    """POST /api/v1/ask-stream — answer a question (SSE stream)."""
    if not request.is_json:
        return jsonify({"error": "Invalid content type. Expected application/json."}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload."}), 400

    query = data.get("query")
    use_llm = data.get("use_llm", True)

    if not query:
        return jsonify({"error": "Query is required."}), 400

    if not isinstance(query, str):
        return jsonify({"error": "Query must be a string."}), 400

    if len(query) > 500:
        return jsonify(
            {"error": "Query is too long. Maximum length is 500 characters."}
        ), 400

    try:
        user_id = request.user.get("user_id")
        events = QAService.answer_query_streaming(query, use_llm=use_llm)

        return Response(
            stream_with_context(_stream_events(user_id, query, use_llm, events)),
            mimetype="text/event-stream",
            headers={
                "X-Accel-Buffering": "no",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    except Exception:
        logger.exception("Error processing streaming query")
        return jsonify({"error": "An error occurred while processing the query."}), 500


def list_messages():
    """GET /api/v1/messages — paginated chat history for the current user."""
    user_id = request.user.get("user_id")
    limit = request.args.get("limit", 20, type=int)
    skip = request.args.get("skip", 0, type=int)
    result = MessageService.get_user_messages(user_id, limit=limit, skip=skip)
    if not result.get("success"):
        return jsonify({"error": result["error"]}), 404
    return jsonify(result), 200


def get_message(message_id: str):
    """GET /api/v1/messages/<id> — single message with populated articles."""
    result = MessageService.get_message(message_id)
    if not result.get("success"):
        return jsonify({"error": result["error"]}), 404
    if result["data"]["user"]["id"] != request.user.get("user_id"):
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(result["data"]), 200


def delete_message(message_id: str):
    """DELETE /api/v1/messages/<id> — delete a single chat message (owner only)."""
    result = MessageService.get_message(message_id)
    if not result.get("success"):
        return jsonify({"error": result["error"]}), 404
    if result["data"]["user"]["id"] != request.user.get("user_id"):
        return jsonify({"error": "Forbidden"}), 403

    delete_result = MessageService.delete_message(message_id)
    return jsonify(delete_result), 200


def delete_all_messages():
    """DELETE /api/v1/messages — delete all chat messages for the current user."""
    user_id = request.user.get("user_id")
    result = MessageService.delete_user_messages(user_id)
    if not result.get("success"):
        return jsonify({"error": result["error"]}), 404
    return jsonify(result), 200
