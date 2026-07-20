import logging
from typing import Optional

from .rag_repository import RAGRepository
from .rag_formatter import RAGFormatter

logger = logging.getLogger(__name__)

_ARTICLE_FIELDS = [
    "doc_id", "part_no", "article_no", "title", "content", "citation",
    "level", "clause_no", "subclause_id", "score",
    "bm25_score", "proximity_score", "title_match_count",
    "matched_terms", "exact_matched_terms", "boost_multiplier",
    "matched_clauses",
]
DEFAULT_RECALL_K = 30
DEFAULT_MAX_CONTEXT = 8


def _build_article_dict(article: dict) -> dict:
    """Return a filtered dict with only the fields the frontend needs."""
    return {k: article.get(k) for k in _ARTICLE_FIELDS}


class RAGWorkflow:
    """Thin Q&A orchestrator: repository → formatter → response assembly."""

    def __init__(
        self,
        repository: RAGRepository,
        formatter: Optional[RAGFormatter] = None,
        max_context_articles: int = DEFAULT_MAX_CONTEXT,
    ):
        self.repo = repository
        self.formatter = formatter or RAGFormatter()
        self.max_context_articles = max_context_articles

    # ------------------------------------------------------------------
    # Question answering (RAG)
    # ------------------------------------------------------------------
    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        """Retrieve articles via the repository (exposed for QAService convenience)."""
        raw = self.repo.retrieve(query, top_k=top_k)
        return self.repo.promote_to_articles(raw)

    def _prepare_articles(self, query: str) -> list[dict]:
        retrieved = self.repo.retrieve(query, top_k=self.max_context_articles)
        promoted = self.repo.promote_to_articles(retrieved)
        for art in promoted:
            art["full_text"] = art["text"]
            art["text"] = self.repo.build_truncated_text(art)
        return promoted

    def ask(
        self,
        query: str,
        use_llm: bool = False,
    ) -> dict:
        """Answer a question using RAG.

        Returns:
            dict with 'query', 'articles', 'response' (optional),
            'ollama_status' (optional), 'citations' (optional), 'error' (optional).
        """
        promoted_articles = self._prepare_articles(query)

        articles = [_build_article_dict(art) for art in promoted_articles]

        result = {"query": query, "articles": articles}

        if not use_llm:
            return result

        is_connected, status_message = self.repo.check_ollama_connection()
        if not is_connected:
            logger.warning("Ollama unavailable: %s", status_message)
            result["ollama_status"] = {
                "connected": False,
                "message": "Ollama service is unavailable.",
            }
            return result

        is_model_available, model_status, available_models = self.repo.check_model_availability()
        if not is_model_available:
            logger.warning("Model unavailable: %s", model_status)
            result["ollama_status"] = {
                "connected": True,
                "model": self.repo.model,
                "model_available": False,
                "message": model_status,
                "available_models": available_models,
            }
            return result

        context = self.formatter.format_context(promoted_articles)
        system_prompt = self.formatter.build_system_prompt()
        user_prompt = self.formatter.build_user_prompt(query, context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.repo.call_llm(messages, stream=False)
            result["response"] = response.message.content

            result["citations"] = [
                {"article": art["citation"], "title": art["title"], "doc_id": art["doc_id"]}
                for art in promoted_articles
            ]
        except Exception as exc:
            logger.exception("LLM call failed after retries")
            result["response"] = f"Error querying LLM: {str(exc)}"
            result["error"] = str(exc)

        result["ollama_status"] = {
            "connected": True,
            "model": self.repo.model,
            "model_available": True,
        }
        return result

    def ask_streaming(self, query: str, use_llm: bool = True):
        """Answer with streaming response (generator yielding events dicts).

        Yields:
            {"type": "articles",  "articles": [...]}
            {"type": "token",     "content": "partial"}
            {"type": "done"}
            # or on error:
            {"type": "error",     "content": "..."}
        """
        promoted_articles = self._prepare_articles(query)

        articles_data = [_build_article_dict(art) for art in promoted_articles]

        yield {"type": "articles", "articles": articles_data}

        if not use_llm:
            yield {"type": "done"}
            return

        is_connected, status_message = self.repo.check_ollama_connection()
        if not is_connected:
            logger.warning("Ollama unavailable: %s", status_message)
            yield {"type": "error", "content": "Ollama service is unavailable."}
            yield {"type": "done"}
            return

        is_model_available, model_status, available_models = self.repo.check_model_availability()
        if not is_model_available:
            logger.warning("Model unavailable: %s", model_status)
            yield {
                "type": "status",
                "connected": True,
                "model": self.repo.model,
                "model_available": False,
                "message": model_status,
                "available_models": available_models,
            }
            yield {"type": "done"}
            return

        context = self.formatter.format_context(promoted_articles)
        system_prompt = self.formatter.build_system_prompt()
        user_prompt = self.formatter.build_user_prompt(query, context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.repo.call_llm(messages, stream=True)
            for part in response:
                if part.message.content:
                    yield {"type": "token", "content": part.message.content}
            yield {"type": "done"}
        except Exception as exc:
            logger.exception("LLM streaming call failed")
            yield {"type": "error", "content": str(exc)}

# Standalone demo
def main():
    from ..core.engine_factory import EngineFactory
    from ..core.reranker import Reranker
    from ..workflows.retrieval_workflow import RetrievalWorkflow

    engine = EngineFactory.from_artifacts(
        "data/output/flattened_nepal_constitution.json",
        "data/output",
        synonyms_path="data/synonyms.json",
    )
    reranker = Reranker(engine.bm25_scorer.tf_index)
    retrieval = RetrievalWorkflow(engine, reranker)
    repo = RAGRepository(retrieval)
    workflow = RAGWorkflow(repo)

    is_connected, msg = workflow.repo.check_ollama_connection()
    print(msg)
    if not is_connected:
        return

    questions = [
        "What are the fundamental rights?",
        "How is the President elected?",
        "What does the constitution say about education?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        result = workflow.ask(q, use_llm=True)
        for art in result["articles"]:
            print(f"  - {art['citation']}: {art['title']} (score={art['score']:.2f})")
        print(f"\nAnswer:\n{result['response']}")


if __name__ == "__main__":
    main()
