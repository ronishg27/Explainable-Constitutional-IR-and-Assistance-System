import logging
from typing import Optional

from src.core.engine_factory import EngineFactory
from src.core.reranker import Reranker
from src.workflows.retrieval_workflow import RetrievalWorkflow
from src.llm.rag_repository import RAGRepository
from src.llm.rag_workflow import RAGWorkflow
from src.llm.rag_formatter import RAGFormatter

from services.article_service import ArticleService
from services.message_service import MessageService

logger = logging.getLogger(__name__)

_DEFAULT_DOCS_PATH = "data/output/flattened_nepal_constitution.json"
_DEFAULT_INDEX_DIR = "data/output"
_DEFAULT_SYNONYMS_PATH = "data/synonyms.json"

_workflow: Optional[RAGWorkflow] = None


def init_workflow() -> None:
    global _workflow
    engine = EngineFactory.from_artifacts(
        _DEFAULT_DOCS_PATH, _DEFAULT_INDEX_DIR,
        synonyms_path=_DEFAULT_SYNONYMS_PATH,
    )
    reranker = Reranker(engine.bm25_scorer.tf_index)
    retrieval_workflow = RetrievalWorkflow(engine, reranker)
    repository = RAGRepository(retrieval_workflow)
    _workflow = RAGWorkflow(repository, RAGFormatter())


class QAService:
    """Service layer for constitution Q&A workflow orchestration."""

    @staticmethod
    def _get_workflow() -> RAGWorkflow:
        return _workflow

    @staticmethod
    def persist_message(user_id: str, query: str, payload: dict) -> None:
        """Save a Q&A exchange to MongoDB. Failures are logged, never break the response."""
        try:
            article_ids = []
            for art in payload.get("articles", []):
                result = ArticleService.create_article(
                    title=str(art.get("title", "")),
                    citation=str(art.get("citation", "")),
                    doc_id=str(art.get("doc_id", "")),
                    relevance_score=art.get("score", 0.0),
                    bm25_score=art.get("bm25_score"),
                    proximity_score=art.get("proximity_score"),
                    title_match_count=art.get("title_match_count"),
                    article_no=art.get("article_no"),
                    clause_no=art.get("clause_no"),
                    subclause_id=art.get("subclause_id"),
                    level=art.get("level"),
                    part_no=art.get("part_no"),
                    content=art.get("content"),
                    text=art.get("text"),
                    full_text=art.get("full_text"),
                    matched_terms=art.get("matched_terms", []),
                    exact_matched_terms=art.get("exact_matched_terms", []),
                )
                if result.get("success"):
                    article_ids.append(result["data"]["id"])
                else:
                    logger.warning("Failed to create article: %s", result.get("error"))

            msg_result = MessageService.create_message(
                user_id=user_id,
                query=query,
                answer=payload.get("response", ""),
                articles=article_ids,
            )
            if not msg_result.get("success"):
                logger.error("Failed to persist message: %s", msg_result.get("error"))
        except Exception as e:
            logger.error("Failed to persist message: %s", e)

    @staticmethod
    def answer_query(query: str, use_llm: bool = False) -> tuple[dict, int]:
        """Return API response payload and HTTP status for a user query."""
        workflow = QAService._get_workflow()
        return workflow.ask(query, use_llm=use_llm), 200

    @staticmethod
    def answer_query_streaming(query: str, use_llm: bool = True):
        workflow = QAService._get_workflow()
        yield from workflow.ask_streaming(query, use_llm=use_llm)
