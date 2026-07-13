import logging
from models.referenced_article_model import ReferencedArticle
from mongoengine.errors import ValidationError, DoesNotExist


logger = logging.getLogger(__name__)

class ArticleService:

    @staticmethod
    def create_article(title:str, citation:str, doc_id:str, relevance_score:float):
        """Create a new referenced article, deduplicating by doc_id."""
        try:
            existing = ReferencedArticle.objects(doc_id=doc_id).first()
            if existing:
                return {
                    'success': True,
                    'message': 'Article already exists',
                    'data': existing.to_json()
                }

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
            logger.exception("Error creating article")
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def get_article(article_id:str):
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
    def list_articles():
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
    def delete_article(article_id:str):
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
            logger.exception("Error deleting article")
            return {
                'success': False,
                'error': str(e)
            }

