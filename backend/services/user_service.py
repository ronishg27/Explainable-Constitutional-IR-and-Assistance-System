import logging
from models.user_model import User
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError

logger = logging.getLogger(__name__)


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
            
        except ValidationError as ve:
            return {
                'success': False,
                'error': f"Validation Error: {str(ve)}",
                'message': 'Invalid user data provided.'
            }
            
        except NotUniqueError as nue:
            return {
                'success': False,
                'message': 'Email already exists',
                'error': f"NotUniqueError: {str(nue)}"
            }
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return {
                'success': False,
                'error': str(e),
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
        except Exception as e:
            logger.error(f"Error retrieving user: {str(e)}")
            return {
                'success': False,
                'error': str(e),
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
        except Exception as e:
            logger.error(f"Error retrieving user by email: {str(e)}")
            return {
                'success': False,
                'error': str(e),
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
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            return {
                'success': False,
                'error': str(e),
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
            
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'An error occurred while deleting the user.'
            }
            
    
    @staticmethod
    def authenticate_user(email: str, password: str):
        """Authenticate a user."""
        try:
            user = User.objects.get(email=email.strip().lower())
            if user.check_password(password):
                return {
                    'success': True,
                    'data': user.to_json(),
                    'message': 'Login successful'
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
        
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'An error occurred during authentication.'
            }
