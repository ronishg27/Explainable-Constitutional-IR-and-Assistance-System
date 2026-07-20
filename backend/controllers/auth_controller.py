import re

from flask import current_app, jsonify, request, make_response, Response
import logging
from models.user_model import RoleEnum, User
from services.user_service import UserService

logger = logging.getLogger(__name__)


def register() -> Response:
    """POST /api/v1/auth/register — create a new user account."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload."}), 400

    fullname = (data.get("fullname") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "user").strip().lower()

    if not fullname or not email :
        return jsonify({"error": "Missing required fields."}), 400

    if len(fullname) > 50:
        return jsonify({"error": "Fullname must not exceed 50 characters."}), 400

    # email validation
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email address."}), 400

    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400

    valid_roles = {e.value for e in RoleEnum}
    if role not in valid_roles:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}), 400

    result = UserService.create_user(fullname, email, password, role)

    if result['success']:
        return jsonify({
            "message": result['message'],
            "user": result['data']
            }), 201
    else:
        return jsonify({
            "error": result['error'],
            "message": result.get('message')
            }), 400


def login() -> Response:
    """POST /api/v1/auth/login — authenticate and return JWT token."""
    data = request.get_json(silent=True)

    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    result = UserService.authenticate_user(email, password)
    if result['success']:
        resp = make_response(jsonify({
            "message": result['message'],
            "user": result['data'],
            "authenticated": True,
            "token": result['token']
            })
        )
        is_production = current_app.config.get('PRODUCTION', False)
        resp.set_cookie('token', result['token'], httponly=True, secure=is_production, samesite='Strict', max_age=60*60*12)
        return resp

    else:
        return jsonify({
            "error": result['error'],
            "message": result.get('message')
            }), 401


def logout() -> Response:
    """POST /api/v1/auth/logout — invalidate session token."""
    user_id = (request.user or {}).get('user_id')
    try:
        user = User.objects.get(id=user_id)
        user.token_version += 1
        user.save()
    except Exception:
        logger.exception("Failed to increment token_version on logout")
        return jsonify({"error": "Logout failed."}), 500

    resp = make_response(jsonify({
        "message": "Logout successful."
        }))
    is_production = current_app.config.get('PRODUCTION', False)
    resp.set_cookie('token', '', expires=0, httponly=True, secure=is_production, samesite='Strict', max_age=-1)
    return resp, 200

def get_current_user() -> Response:
    """GET /api/v1/auth/me — return profile of the authenticated user."""
    user_id = (request.user or {}).get('user_id')
    user = UserService.get_user(user_id)
    if user:
        return jsonify(user), 200

    return jsonify({
        "error": "User not found."
    }), 404

