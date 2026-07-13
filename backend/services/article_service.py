import logging
from models.referenced_article_model import ReferencedArticle
from mongoengine.errors import ValidationError, DoesNotExist


logger = logging.getLogger(__name__)

class ArticleService:

    @staticmethod
    def create_article(title, citation, doc_id, relevance_score,
                       article_no=None, clause_no=None, subclause_id=None,
                       level=None, part_no=None, text=None,
                       bm25_score=None, proximity_score=None, title_match_count=None):
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
                relevance_score=relevance_score,
                bm25_score=bm25_score or 0.0,
                proximity_score=proximity_score or 0.0,
                title_match_count=title_match_count or 0,
                article_no=article_no,
                clause_no=clause_no,
                subclause_id=subclause_id,
                level=level,
                part_no=part_no,
                text=text,
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

