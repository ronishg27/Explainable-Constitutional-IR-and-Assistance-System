from models.user_model import User
from models.referenced_article_model import ReferencedArticle
from models.message_model import Message
from mongoengine.errors import DoesNotExist, ValidationError
from typing import List, Any

import logging



logger = logging.getLogger(__name__)


class MessageService:
    """Handles chat messages with referenced articles."""
    
    @staticmethod
    async def create_message(
            user_id:str,
            query:str,
            answer:str,
            articles: List[Any] = None #TODO: Define a proper type for articles (List[ReferencedArticle]
        ):
        """Create a new message with referenced articles."""
        try:
            
            # 1. get the user 
            user = User.objects.get(id=user_id)
            
            # 2. Get the referenced articles (if any)
            
            article_refs = []
            if articles:
                for art_id in articles:
                    try: 
                        article = ReferencedArticle.objects.get(id=art_id)
                        article_refs.append(article)
                    except DoesNotExist:
                        logger.warning(f"Referenced article with id {art_id} not found. Skipping.")
                        
            # 3. Create the message
            message = Message(
                query=query,
                answer=answer,
                user= user,
                articles = article_refs
            )
            
            message.save()
            
            return {
                'success': True,
                'message': 'Message created successfully',
                'data': message.to_json()
            }
            
        except DoesNotExist:
            return {
                'success': False,
                'error': 'User not found'
            }
        
        except ValidationError as ve:
            return {
                'success': False,
                'error': f'Validation error: {str(ve)}'
            }
            
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
            
    @staticmethod
    async def get_user_messages(user_id:str, limit:int=20, skip:int=0):
        """Get all messages for a specific user."""
        try:
            # 1. Get the user
            user = User.objects.get(id=user_id)
            
            # 2. Get messages for the user with pagination
            messages = Message.objects(user=user)\
                .order_by('-created_at')\
                .skip(skip)\
                .limit(limit)
            
            # 3. get the total count for pagination
            total_count = Message.objects(user=user).count()
            
            return {
                'success': True,
                'data': [msg.to_json() for msg in messages],
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'skip': skip,
                    'has_more': skip + limit < total_count
                }
            }
            
        except DoesNotExist:
            return {
                'success': False,
                'error': 'User not found'
            }
            
    @staticmethod
    async def get_message(message_id:str):
        """Get a single message by ID."""
        try:
            message = Message.objects.get(id=message_id)
            return {
                'success': True,
                'data': message.to_json()
            }
        except DoesNotExist:
            return {
                'success': False,
                'error': 'Message not found'
            }
            
    @staticmethod
    async def update_message_answer(message_id:str, new_answer:str):
        """Update the answer of a message."""
        try:
            message = Message.objects.get(id=message_id)
            message.answer = new_answer
            message.save()
            return {
                'success': True,
                'message': 'Message answer updated successfully',
                'data': message.to_json()
            }
        except DoesNotExist:
            return {
                'success': False,
                'error': 'Message not found'
            }
            
    
    @staticmethod
    async def search_messages(user_id:str, search_term:str):
        """Search messages by query text"""
        try:
            user = User.objects.get(id=user_id)
            
            # case-insensitive search in the query field
            messages = Message.objects(
                user=user,
                query_iscontains=search_term
            ).order_by('-created_at')
            
            return {
                'success': True,
                'data': [msg.to_json() for msg in messages],
                'count': messages.count()
            }
        except DoesNotExist:
            return {
                'success': False,
                'error': 'User not found'
            }
            
    @staticmethod
    async def delete_message(message_id:str):
        """Delete a message by ID."""
        try:
            message = Message.objects.get(id=message_id)
            message.delete()
            return {
                'success': True,
                'message': 'Message deleted successfully'
            }
        except DoesNotExist:
            return {
                'success': False,
                'error': 'Message not found'
            }
    
    @staticmethod
    async def delete_user_messages(user_id:str):
        """Delete all messages for a specific user."""
        try:
            user = User.objects.get(id=user_id)
            deleted_count = Message.objects(user=user).delete()
            return {
                'success': True,
                'message': f'{deleted_count} messages deleted successfully'
            }
        except DoesNotExist:
            return {
                'success': False,
                'error': 'User not found'
            }