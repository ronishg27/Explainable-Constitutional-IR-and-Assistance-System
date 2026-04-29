"""
RAG (Retrieval-Augmented Generation) Workflow for Constitution Q&A.

Combines document retrieval with LLM to answer questions about the constitution
with accurate citations.
"""

import logging
from typing import Any, Optional

from .ollama_llm import createOllamaClient
from .rag_formatter import RAGFormatter
from .rag_repository import RAGRepository

logger = logging.getLogger(__name__)


class RAGWorkflow:
    """Retrieval-Augmented Generation workflow for constitution QA."""

    def __init__(
        self,
        documents_path: Optional[str] = None,
        ollama_host: Optional[str] = None,
        model: str = "gemma3:1b",
        max_context_articles: int = 5,
        title_boost: float = 5.0,
    ):
        """
        Initialize RAG workflow.

        Args:
            documents_path: Path to flattened constitution JSON. If None, uses default.
            ollama_host: Ollama API endpoint. If None, uses OLLAMA_HOST env var.
            model: Ollama model name to use.
            max_context_articles: Max articles to include in LLM context.
            title_boost: Title matching boost factor for BM25.
        """
        self.repository = RAGRepository(
            documents_path=documents_path,
            title_boost=title_boost,
            max_context_articles=max_context_articles,
        )
        self.documents_path = self.repository.documents_path
        self.model = model
        self.max_context_articles = max_context_articles
        self.title_boost = title_boost
        self.ollama_host = ollama_host
        self.client = createOllamaClient()
        self.formatter = RAGFormatter()

    def _extract_model_names(self, models_response: Any) -> list[str]:
        """Normalize model names from Ollama list response shapes."""
        model_names: list[str] = []

        if isinstance(models_response, dict):
            model_items = models_response.get("models", [])
        else:
            model_items = getattr(models_response, "models", [])

        for model_item in model_items or []:
            if isinstance(model_item, dict):
                name = model_item.get("model") or model_item.get("name")
            else:
                name = getattr(model_item, "model", None) or getattr(model_item, "name", None)

            if isinstance(name, str) and name:
                model_names.append(name)

        return model_names

    def check_ollama_connection(self) -> tuple[bool, str]:
        """Check whether Ollama is reachable and report status."""
        try:
            models_response = self.client.list()
            model_names = self._extract_model_names(models_response)
            if model_names:
                return True, f"Connected to Ollama. Found {len(model_names)} model(s)."
            return True, "Connected to Ollama. No local models listed."
        except Exception as exc:
            return False, (
                "Could not connect to Ollama. Start it with 'ollama serve' "
                "or set OLLAMA_HOST to the correct endpoint. "
                f"Details: {exc}"
            )

    def check_model_availability(self, model_name: Optional[str] = None) -> tuple[bool, str, list[str]]:
        """Check whether the requested model exists in local Ollama models."""
        target_model = model_name or self.model

        try:
            models_response = self.client.list()
            available_models = self._extract_model_names(models_response)

            if target_model in available_models:
                return True, f"Model '{target_model}' is available.", available_models

            return (
                False,
                f"Model '{target_model}' is unavailable in local Ollama models.",
                available_models,
            )
        except Exception as exc:
            return False, f"Could not verify model availability. Details: {exc}", []

    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        """
        Retrieve relevant articles using BM25.

        Args:
            query: User question or search query.
            top_k: Number of articles to retrieve. Uses max_context_articles if None.

        Returns:
            List of retrieved articles with scores.
        """
        if top_k is None:
            top_k = self.max_context_articles

        results = self.repository.retrieve(query, top_k=top_k)

        if not results:
            logger.info(
                "No articles crossed relevance threshold (score > 0). query='%s', top_k=%s",
                query,
                top_k,
            )

        return results

    def ask(
        self,
        query: str,
        stream: bool = False,
        retrieve_only: bool = False,
    ) -> dict:
        """
        Answer a question using RAG workflow.

        Args:
            query: User question.
            stream: If True, return streamed response. If False, return full response.
            retrieve_only: If True, return only retrieved articles without LLM answer.
            useLLM: If True, use the LLM to generate the answer. If False, return only the retrieved articles.  
        Returns:
            Dict with 'query', 'retrieved_articles', 'answer', and 'citations'.
        """
        retrieved_articles = self.retrieve(query)

        result = {
            "query": query,
            "retrieved_articles": [
                {
                    "doc_id": art["doc_id"],
                    "article_no": art["article_no"],
                    "title": art["title"],
                    "citation": art["citation"],
                    "score": art.get("score", 0.0),
                }
                for art in retrieved_articles
            ],
            "answer": None,
            "citations": [],
        }

        if retrieve_only:
            return result

        context = self.formatter.format_context(retrieved_articles)
        prompt = self.formatter.build_prompt(query, context)

        try:
            messages = [{"role": "user", "content": prompt}]

            if stream:
                def stream_response():
                    for part in self.client.chat(
                        self.model,
                        messages=messages,
                        stream=True,
                    ):
                        yield part.message.content

                result["answer"] = stream_response()
            else:
                response = self.client.chat(
                    self.model,
                    messages=messages,
                    stream=False,
                )
                result["answer"] = response.message.content

            result["citations"] = [
                {
                    "article": art["citation"],
                    "title": art["title"],
                    "doc_id": art["doc_id"],
                }
                for art in retrieved_articles
            ]

        except Exception as exc:
            result["answer"] = f"Error querying LLM: {str(exc)}"
            result["error"] = str(exc)

        return result

    def ask_streaming(self, query: str):
        """
        Answer a question with streaming response.

        Args:
            query: User question.

        Yields:
            Streamed response chunks from LLM.
        """
        retrieved_articles = self.retrieve(query)
        context = self.formatter.format_context(retrieved_articles)
        prompt = self.formatter.build_prompt(query, context)

        messages = [{"role": "user", "content": prompt}]

        try:
            for part in self.client.chat(
                self.model,
                messages=messages,
                stream=True,
            ):
                yield part.message.content
        except Exception as exc:
            yield f"Error: {str(exc)}"


def main():
    """Demo: Run RAG workflow on sample questions."""
    workflow = RAGWorkflow()

    is_connected, status_message = workflow.check_ollama_connection()
    questions = [
        "What are the fundamental rights in the constitution?",
        "How is the President elected?",
        "What does the constitution say about education?",
    ]

    print("=" * 80)
    print("CONSTITUTION Q&A WITH RAG")
    print("=" * 80)
    print(status_message)
    print("=" * 80)

    if not is_connected:
        return

    for question in questions:
        print(f"\nQ: {question}")
        print("-" * 80)

        result = workflow.ask(question, stream=False)

        print("\nRetrieved Articles:")
        for art in result["retrieved_articles"]:
            print(f"  - {art['citation']}: {art['title']} (score: {art['score']:.2f})")

        print(f"\nAnswer:\n{result['answer']}")
        print("-" * 80)


if __name__ == "__main__":
    main()
