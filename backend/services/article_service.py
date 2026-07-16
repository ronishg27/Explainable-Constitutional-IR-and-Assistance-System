import logging
from models.referenced_article_model import ReferencedArticle
from mongoengine.errors import ValidationError, DoesNotExist


logger = logging.getLogger(__name__)

class ArticleService:

    @staticmethod
    def create_article(title, citation, doc_id, relevance_score,
                       article_no=None, clause_no=None, subclause_id=None,
                       level=None, part_no=None, text=None, full_text=None,
                       bm25_score=None, proximity_score=None, title_match_count=None,
                       matched_terms=None, exact_matched_terms=None):
        """Create or update a referenced article, deduplicating by doc_id."""
        try:
            existing = ReferencedArticle.objects(doc_id=doc_id).first()
            if existing:
                existing.text = text
                existing.full_text = full_text
                existing.matched_terms = matched_terms or []
                existing.exact_matched_terms = exact_matched_terms or []
                existing.relevance_score = relevance_score
                existing.bm25_score = bm25_score or 0.0
                existing.proximity_score = proximity_score or 0.0
                existing.title_match_count = title_match_count or 0
                existing.save()
                return {
                    'success': True,
                    'message': 'Article updated',
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
                full_text=full_text,
                matched_terms=matched_terms or [],
                exact_matched_terms=exact_matched_terms or [],
            )
            article.save()

            return {
                'success': True,
                'message': 'Article created successfully',
                'data': article.to_json()
            }

        except ValidationError:
            return {
                'success': False,
                'error': 'Validation error'
            }
        except Exception:
            logger.exception("Error creating article")
            return {
                'success': False,
                'error': 'An error occurred while creating the article.'
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
        except Exception:
            logger.exception("Error retrieving article")
            return {
                'success': False,
                'error': 'An error occurred while retrieving the article.'
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
        except Exception:
            logger.exception("Error listing articles")
            return {
                'success': False,
                'error': 'An error occurred while listing articles.'
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
        except Exception:
            logger.exception("Error deleting article")
            return {
                'success': False,
                'error': 'An error occurred while deleting the article.'
            }

