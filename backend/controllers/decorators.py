import jwt
from functools import wraps
from typing import Optional
from flask import request, jsonify
import os
import logging

from mongoengine.connection import get_db, ConnectionFailure

logger = logging.getLogger(__name__)


def _get_user(user_id: str) -> Optional[object]:
    """Look up a user by ID, returning None if the DB is unavailable."""
    try:
        get_db()
    except ConnectionFailure:
        logger.warning("Database not available; skipping token_version check.")
        return None
    except Exception:
        logger.warning("Could not connect to database; skipping token_version check.")
        return None

    try:
        from models.user_model import User
        return User.objects(id=user_id).first()
    except Exception:
        return None


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif request.cookies.get('token'):
            token = request.cookies.get('token')

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        JWT_SECRET = os.getenv('JWT_SECRET')
        if not JWT_SECRET:
            return jsonify({'error': 'JWT_SECRET is not set in environment variables!'}), 500

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

            user = _get_user(payload.get('user_id'))
            if user is None:
                pass
            else:
                token_version = payload.get('token_version', -1)
                if token_version < user.token_version:
                    return jsonify({'error': 'Token has been invalidated. Please log in again.'}), 401

            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401
        except Exception as e:
            logger.exception("Token validation error")
            return jsonify({'error': 'An error occurred while validating the token.'}), 500

        return f(*args, **kwargs)

    return decorated

