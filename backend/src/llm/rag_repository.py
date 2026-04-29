from typing import Optional

from ..workflows.ingestion_workflow import IngestionWorkflow
from ..workflows.retrieval_workflow import RetrievalWorkflow


class RAGRepository:
    """Bridges ingestion and retrieval workflows for RAG."""

    def __init__(
        self,
        documents_path: Optional[str] = None,
        title_boost: float = 5.0,
        max_context_articles: int = 5,
    ):
        self.ingestion = IngestionWorkflow(documents_path=documents_path)
        self.documents_path = self.ingestion.documents_path
        self.title_boost = title_boost
        self.max_context_articles = max_context_articles
        self.documents, self.bm25 = self.ingestion.build_retrieval_state()
        self.retrieval = RetrievalWorkflow(
            documents=self.documents,
            bm25=self.bm25,
            title_boost=title_boost,
            max_context_articles=max_context_articles,
        )

    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        return self.retrieval.retrieve(query, top_k=top_k)
