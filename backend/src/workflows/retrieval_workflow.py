from typing import Optional

from ..core.bm25 import BM25, search_bm25_with_boost


class RetrievalWorkflow:
    """Handles retrieval/ranking from prepared BM25 state."""

    def __init__(
        self,
        documents: list[dict],
        bm25: BM25,
        title_boost: float = 5.0,
        max_context_articles: int = 5,
    ):
        self.documents = documents
        self.bm25 = bm25
        self.title_boost = title_boost
        self.max_context_articles = max_context_articles

    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        if top_k is None:
            top_k = self.max_context_articles

        return search_bm25_with_boost(
            query,
            self.bm25,
            self.documents,
            title_boost=self.title_boost,
            top_k=top_k,
        )
