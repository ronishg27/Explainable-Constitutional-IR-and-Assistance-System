from flask import jsonify, request
import logging
import asyncio
from services.user_service import UserService

logger = logging.getLogger(__name__)


def register():
    """Handle user registration."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload."}), 400
    
    fullname = data.get("fullname").strip()
    email = data.get("email").strip().lower()
    password = data.get("password").strip()
    role = data.get("role", "user").strip().lower()
    
    if not fullname or not email :
        return jsonify({"error": "Missing required fields."}), 400
    
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400
    
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


def login():
    """Handle user login."""
    data = request.get_json(silent=True)
    
    email = data.get("email").strip().lower()
    password = data.get("password").strip()
    
    result = asyncio.run(UserService.authenticate_user(email, password))
    if result['success']:
        return jsonify({
            "message": result['message'],
            "user": result['data'],
            "authenticated": True
            }), 200
    else:
        return jsonify({
            "error": result['error'],
            "message": result.get('message')
            }), 401



def logout():
    return jsonify({
        "message": "Logout endpoint is not implemented yet."
        }), 501



