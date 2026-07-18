from ..core.search_engine import SearchEngine
from ..core.reranker import Reranker


class RetrievalWorkflow:
    """Canonical runtime retrieval pipeline: high-recall search → reranking → top-k.

    Composes SearchEngine and Reranker into a single workflow step.
    """

    def __init__(
        self,
        search_engine: SearchEngine,
        reranker: Reranker,
        default_recall_k: int = 50,
        default_top_k: int = 8,
    ):
        self.engine = search_engine
        self.reranker = reranker
        self.default_recall_k = default_recall_k
        self.default_top_k = default_top_k

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        boost_rules: dict | None = None,
    ) -> list[dict]:
        """Run full retrieval pipeline: high-recall search → rerank → results.

        Args:
            query: User question.
            top_k: Number of final results to return (default default_top_k).
            boost_rules: Optional rule-based boost configuration.

        Returns:
            Reranked list of article dicts.
        """
        recall_k = self.default_recall_k
        final_k = top_k or self.default_top_k

        initial_results = self.engine.search(query, top_k=recall_k)
        if not initial_results:
            return []

        return self.reranker.rerank(initial_results, top_k=final_k, boost_rules=boost_rules)
