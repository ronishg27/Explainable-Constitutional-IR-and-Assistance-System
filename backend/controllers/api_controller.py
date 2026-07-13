import json
import logging
import time

from flask import Response, jsonify, request, stream_with_context

from services.article_service import ArticleService
from services.message_service import MessageService
from services.qa_service import QAService

logger = logging.getLogger(__name__)


def _persist_message(user_id: str, query: str, payload: dict) -> None:
    """Save a Q&A exchange to MongoDB. Failures are logged, never break the response."""
    try:
        article_ids = []
        for art in payload.get("articles", []):
            result = ArticleService.create_article(
                title=str(art.get("title", "")),
                citation=str(art.get("citation", "")),
                doc_id=str(art.get("doc_id", "")),
                relevance_score=art.get("score", 0.0),
            )
            if result.get("success"):
                article_ids.append(result["data"]["id"])
            else:
                logger.warning("Failed to create article: %s", result.get("error"))

        msg_result = MessageService.create_message(
            user_id=user_id,
            query=query,
            answer=payload.get("response", ""),
            articles=article_ids,
        )
        if not msg_result.get("success"):
            logger.error("Failed to persist message: %s", msg_result.get("error"))
    except Exception as e:
        logger.error("Failed to persist message: %s", e)


def home():
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
            },
            "version": "1.0.0",
        }
    )


def health():
    return jsonify({"status": "healthy"})


def ask():
    start = time.time()
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

        if status_code == 200:
            user_id = request.user.get("user_id")
            _persist_message(user_id, query, payload)

        elapsed = time.time() - start
        logger.info(
            "query=%s use_llm=%s status=%d latency=%.2fs",
            query[:80], useLLM, status_code, elapsed,
        )
        return jsonify(payload), status_code
    except Exception:
        logger.exception("Error processing query")
        return jsonify({"error": "An error occurred while processing the query."}), 500


def ask_stream():
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

        def generate():
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
                    _persist_message(user_id, query, payload)
                    elapsed = time.time() - stream_start
                    logger.info(
                        "stream query=%s use_llm=%s latency=%.2fs",
                        query[:80], use_llm, elapsed,
                    )

                yield f"data: {json.dumps(event)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "X-Accel-Buffering": "no",
                "Cache-Control": "no-cache",
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
