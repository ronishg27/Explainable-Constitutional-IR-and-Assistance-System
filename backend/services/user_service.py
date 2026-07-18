import logging
from models.user_model import User
import jwt
import os
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError

logger = logging.getLogger(__name__)


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is required")
    return secret


class UserService:

    @staticmethod
    def create_user(fullname:str, email:str, password:str, role:str='user'):
        "Create a new user."
        try:
            user = User(
                fullname = fullname.strip(),
                email = email.strip().lower(),
                role = role.strip().lower() if role else 'user',
            )
            user.set_password(password.strip())
            user.save()


            return {
                'success': True,
                'message': 'User created successfully',
                'data': user.to_json()
            }

        except ValidationError:
            return {
                'success': False,
                'error': 'Invalid user data provided.',
                'message': 'Invalid user data provided.'
            }

        except NotUniqueError:
            return {
                'success': False,
                'message': 'Email already exists',
                'error': 'Email already exists'
            }
        except Exception:
            logger.exception("Error creating user")
            return {
                'success': False,
                'error': 'An error occurred while creating the user.',
                'message': 'An error occurred while creating the user.'
            }

    @staticmethod
    def get_user(user_id: str):
        """Retrieve a user by their ID."""
        try:
            user = User.objects.get(id=user_id)
            return {
                'success': True,
                'data': user.to_json(),
                'message': 'User retrieved successfully'
            }
        except DoesNotExist:
            return {
                'success': False,
                'error': 'User not found',
                'message': 'No user exists with the provided ID.',
            }
        except Exception:
            logger.exception("Error retrieving user")
            return {
                'success': False,
                'error': 'An error occurred while retrieving the user.',
                "message": 'An error occurred while retrieving the user.'
            }

    @staticmethod
    def get_user_by_email(email: str):
        """Retrieve a user by their email."""
        try:
            user = User.objects.get(email=email.strip().lower())
            return {
                'success': True,
                'data': user.to_json(),
                'message': 'User retrieved successfully'
            }
        except DoesNotExist:
            return {
                'success': False,
                'error': 'User not found',
                'message': 'No user exists with the provided email.'
            }
        except Exception:
            logger.exception("Error retrieving user by email")
            return {
                'success': False,
                'error': 'An error occurred while retrieving the user.',
                "message": 'An error occurred while retrieving the user.'
            }


    @staticmethod
    def list_users():
        """List all users."""
        try:
            users = User.objects()
            return {
                'success': True,
                'data': [user.to_json() for user in users],
                'message': 'Users retrieved successfully'
            }
        except Exception:
            logger.exception("Error listing users")
            return {
                'success': False,
                'error': 'An error occurred while listing users.',
                'message': 'An error occurred while listing users.'
            }

    @staticmethod
    def delete_user(user_id: str):
        """Delete a user by their ID."""
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return {
                'success': True,
                'message': 'User deleted successfully'
            }
        except DoesNotExist:
            return {
                'success': False,
                'error': 'User not found',
                'message': 'No user exists with the provided ID.'
            }

        except Exception:
            logger.exception("Error deleting user")
            return {
                'success': False,
                'error': 'An error occurred while deleting the user.',
                'message': 'An error occurred while deleting the user.'
            }


    @staticmethod
    def authenticate_user(email: str, password: str):
        """Authenticate a user."""
        try:
            user = User.objects.get(email=email.strip().lower())
            if user.check_password(password):
                payload = {
                    'user_id': str(user.id),
                    'email': user.email,
                    'token_version': user.token_version,
                }
                token = jwt.encode(payload, _get_jwt_secret(), algorithm='HS256')
                return {
                    'success': True,
                    'data': user.to_json(),
                    'message': 'Login successful',
                    'token': token
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid credentials',
                    'message': 'Incorrect email or password.'
                }

        except DoesNotExist:
            return {
                'success': False,
                'error': 'User not found',
                'message': 'No user exists with the provided email.'
            }

        except Exception:
            logger.exception("Error authenticating user")
            return {
                'success': False,
                'error': 'An error occurred during authentication.',
                'message': 'An error occurred during authentication.'
            }

