from flask import Blueprint
from controllers.auth_controller import get_current_user, register, login, logout
from controllers.decorators import token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/register", methods=["POST"])
def register_user():
    return register()


@auth_bp.route("/login", methods=["POST"])
def login_user():
    return login()


# TODO: Implement Protected route and token-based authentication before enabling logout
@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout_user():
    return logout()

@auth_bp.route("/me", methods=["GET"])
@token_required
def get_logged_in_user():
    return get_current_user()

