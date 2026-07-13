import logging
import os
from typing import Any, Optional

from .rag_repository import RAGRepository
from .rag_formatter import RAGFormatter

logger = logging.getLogger(__name__)

_ARTICLE_FIELDS = [
    "doc_id", "part_no", "article_no", "title", "text", "full_text", "citation",
    "level", "clause_no", "subclause_id", "score",
    "bm25_score", "proximity_score", "title_match_count",
]
DEFAULT_RECALL_K = 30
DEFAULT_MAX_CONTEXT = 8


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

    @staticmethod
    def _build_article_dict(article: dict) -> dict:
        """Return a filtered dict with only the fields the frontend needs."""
        return {k: article.get(k) for k in _ARTICLE_FIELDS}

    def ask(
        self,
        query: str,
        retrieve_only: bool = False,
    ) -> dict:
        """Answer a question using RAG.

        Returns:
            dict with 'query', 'retrieved_articles', 'answer' (optional), 'citations' (optional).
        """
        retrieved_articles = self.repo.retrieve(query, top_k=self.max_context_articles)
        promoted_articles = self.repo.promote_to_articles(retrieved_articles)

        for art in promoted_articles:
            art["full_text"] = art["text"]
            art["text"] = self.repo.build_truncated_text(art)

        result = {
            "query": query,
            "retrieved_articles": [
                self._build_article_dict(art) for art in promoted_articles
            ],
        }

        if retrieve_only:
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
            result["answer"] = response.message.content

            result["citations"] = [
                {"article": art["citation"], "title": art["title"], "doc_id": art["doc_id"]}
                for art in promoted_articles
            ]
        except Exception as exc:
            logger.exception("LLM call failed after retries")
            result["answer"] = f"Error querying LLM: {str(exc)}"
            result["error"] = str(exc)

        return result

    def ask_streaming(self, query: str):
        """Answer with streaming response (generator yielding events dicts).

        Yields:
            {"type": "articles",  "articles": [...]}
            {"type": "token",     "content": "partial"}
            {"type": "done"}
            # or on error:
            {"type": "error",     "content": "..."}
        """
        retrieved_articles = self.repo.retrieve(query, top_k=self.max_context_articles)
        promoted_articles = self.repo.promote_to_articles(retrieved_articles)

        for art in promoted_articles:
            art["full_text"] = art["text"]
            art["text"] = self.repo.build_truncated_text(art)

        articles_data = [self._build_article_dict(art) for art in promoted_articles]

        yield {"type": "articles", "articles": articles_data}

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

    # ------------------------------------------------------------------
    # Convenience proxies for QAService
    # ------------------------------------------------------------------
    @property
    def model(self) -> str:
        return self.repo.model

    def check_ollama_connection(self) -> tuple[bool, str]:
        return self.repo.check_ollama_connection()

    def check_model_availability(self, model_name: Optional[str] = None) -> tuple[bool, str, list[str]]:
        return self.repo.check_model_availability(model_name)


# Standalone demo
def main():
    from ..core.engine_factory import EngineFactory
    from ..core.reranker import Reranker
    from ..workflows.retrieval_workflow import RetrievalWorkflow

    engine = EngineFactory.from_artifacts(
        "data/output/flattened_nepal_constitution.json",
        "data/output",
    )
    reranker = Reranker(engine.bm25_scorer.tf_index)
    retrieval = RetrievalWorkflow(engine, reranker)
    repo = RAGRepository(retrieval)
    workflow = RAGWorkflow(repo)

    is_connected, msg = workflow.check_ollama_connection()
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
        result = workflow.ask(q)
        for art in result["retrieved_articles"]:
            print(f"  - {art['citation']}: {art['title']} (score={art['score']:.2f})")
        print(f"\nAnswer:\n{result['answer']}")


if __name__ == "__main__":
    main()
