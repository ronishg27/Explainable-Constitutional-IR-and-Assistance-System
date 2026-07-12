from flask import Blueprint

from controllers.api_controller import ask, ask_stream, get_message, health, home, list_messages
from controllers.decorators import token_required


api_bp = Blueprint("api", __name__)


@api_bp.route("/api/v1", methods=["GET"])
def home_route():
    return home()


@api_bp.route("/api/v1/health", methods=["GET"])
def health_route():
    return health()

@api_bp.route("/api/v1/ask", methods=["POST"])
@token_required
def ask_route():
    return ask()


@api_bp.route("/api/v1/ask-stream", methods=["POST"])
@token_required
def ask_stream_route():
    return ask_stream()


@api_bp.route("/api/v1/messages", methods=["GET"])
@token_required
def list_messages_route():
    return list_messages()


@api_bp.route("/api/v1/messages/<message_id>", methods=["GET"])
@token_required
def get_message_route(message_id):
    return get_message(message_id)