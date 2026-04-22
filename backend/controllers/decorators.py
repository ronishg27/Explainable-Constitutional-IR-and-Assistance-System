import jwt
from functools import wraps
from flask import request, jsonify, make_response
import os


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token is missing!'}), 401
        
        token = auth_header.split(' ')[1]
        JWT_SECRET = os.getenv('JWT_SECRET')
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