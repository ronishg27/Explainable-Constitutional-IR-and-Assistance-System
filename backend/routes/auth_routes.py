from flask import Blueprint
from controllers.auth_controller import register, login, logout

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/register", methods=["POST"])
def register_user():
    return register()


@auth_bp.route("/login", methods=["POST"])
def login_user():
    return login()


# TODO: Implement Protected route and token-based authentication before enabling logout
@auth_bp.route("/logout", methods=["POST"])
def logout_user():
    return logout()


