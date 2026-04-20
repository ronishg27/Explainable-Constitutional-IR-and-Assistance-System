from flask import Blueprint

from controllers.api_controller import ask, health, home


api_bp = Blueprint("api", __name__)


@api_bp.route("/api/v1", methods=["GET"])
def home_route():
    return home()


@api_bp.route("/api/v1/health", methods=["GET"])
def health_route():
    return health()


@api_bp.route("/api/v1/ask", methods=["POST"])
def ask_route():
    return ask()
