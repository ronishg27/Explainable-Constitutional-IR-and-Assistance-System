import logging
from models.referenced_article_model import ReferencedArticle
from mongoengine.errors import ValidationError, DoesNotExist



logger = logging.getLogger(__name__)

class ArticleService:
    
    @staticmethod
    async def create_article(title:str, citation:str, doc_id:str, relevance_score:float):
        """Create a new referenced article."""
        try:
            article = ReferencedArticle(
                title=title,
                citation=citation,
                doc_id=doc_id,
                relevance_score=relevance_score
            )
            article.save()
            
            return {
                'success': True,
                'message': 'Article created successfully',
                'data': article.to_json()
            }
            
        except ValidationError as ve:
            return {
                'success': False,
                'error': f"Validation Error: {str(ve)}"
            }
        except Exception as e:
            logger.error(f"Error creating article: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
    @staticmethod
    async def get_article(article_id:str):
        """Retrieve an article by its ID."""
        try:
            article = ReferencedArticle.objects.get(id=article_id)
            return {
                'success': True,
                'data': article.to_json()
            }
            
        except DoesNotExist:
            return {
                'success': False,
                'error': 'Article not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    @staticmethod 
    async def list_articles():
        """List all referenced articles."""
        try:
            articles = ReferencedArticle.objects()
            return {
                'success': True,
                'data': [article.to_json() for article in articles]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    async def delete_article(article_id:str):
        """Delete an article by its ID."""
        try:
            article = ReferencedArticle.objects.get(id=article_id)
            article.delete()
            return {
                'success': True,
                'message': 'Article deleted successfully'
            }
        except DoesNotExist:
            return {
                'success': False,
                'error': 'Article not found'
            }
        except Exception as e:
            logger.error(f"Error deleting article: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    