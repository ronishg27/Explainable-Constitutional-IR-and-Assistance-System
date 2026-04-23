import jwt
from functools import wraps
from flask import request, jsonify
import os


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
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401
        except Exception as e:
            return jsonify({'error': f'An error occurred: {str(e)}'}), 500
        
        return f(*args, **kwargs)
    
    return decorated