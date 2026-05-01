# src/llm/rag_workflow.py
"""
RAG (Retrieval-Augmented Generation) Workflow for Constitution Q&A.

Combines the SearchEngine with an LLM to answer questions using
only the provided constitutional articles.
"""

import logging
import os
import time
from typing import Any, Optional

from .ollama_llm import createOllamaClient
from .rag_formatter import RAGFormatter
from ..core.search_engine import SearchEngine

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemma3:1b"
RETRY_ATTEMPTS = 3
RETRY_DELAY = 0.5  # seconds


class RAGWorkflow:
    """Retrieval-Augmented Generation workflow for constitution QA."""

    def __init__(
        self,
        engine: SearchEngine,
        model: Optional[str] = None,
        max_context_articles: int = 5,
    ):
        """
        Args:
            engine: A fully initialised SearchEngine (created by EngineFactory).
            model: Ollama model name (defaults to OLLAMA_MODEL env or 'gemma3:1b').
            max_context_articles: Maximum articles to include in LLM context.
        """
        self.engine = engine
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self.max_context_articles = max_context_articles
        self.client = createOllamaClient()
        self.formatter = RAGFormatter()

        # Cached connectivity info (lazy, checked once)
        self._ollama_available: Optional[bool] = None
        self._available_models: list[str] = []
        self._connection_status: str = "Not checked yet."

    # ------------------------------------------------------------------
    # Ollama connectivity helpers (with caching)
    # ------------------------------------------------------------------
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

    def _perform_ollama_check(self) -> tuple[bool, str]:
        """Actually perform the Ollama connectivity check (called only once)."""
        try:
            models_response = self.client.list()
            model_names = self._extract_model_names(models_response)
            self._available_models = model_names
            if model_names:
                return True, f"Connected to Ollama. Found {len(model_names)} model(s)."
            return True, "Connected to Ollama. No local models listed."
        except Exception as exc:
            return False, (
                "Could not connect to Ollama. Start it with 'ollama serve' "
                f"or set OLLAMA_HOST. Details: {exc}"
            )

    def _ensure_ollama_checked(self) -> None:
        """Check Ollama once and cache the results."""
        if self._ollama_available is None:
            logger.info("Performing initial Ollama connectivity check...")
            self._ollama_available, self._connection_status = self._perform_ollama_check()
            if self._ollama_available:
                logger.info(self._connection_status)
            else:
                logger.warning(self._connection_status)

    def check_ollama_connection(self) -> tuple[bool, str]:
        """Public method that returns cached or fresh connectivity status."""
        self._ensure_ollama_checked()
        return self._ollama_available, self._connection_status

    def check_model_availability(self, model_name: Optional[str] = None) -> tuple[bool, str, list[str]]:
        """Check whether the requested model exists (uses cached model list)."""
        self._ensure_ollama_checked()
        target = model_name or self.model

        if not self._ollama_available:
            return False, "Ollama is not reachable.", self._available_models

        if target in self._available_models:
            return True, f"Model '{target}' is available.", self._available_models
        return False, f"Model '{target}' is unavailable.", self._available_models

    # ------------------------------------------------------------------
    # Core retrieval (thin wrapper around SearchEngine)
    # ------------------------------------------------------------------
    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        """
        Retrieve relevant articles using the search engine.

        Returns:
            List of article dicts with keys: doc_id, title, citation, text, score, ...
        """
        k = top_k or self.max_context_articles
        results = self.engine.search(query, top_k=k)
        if not results:
            logger.info("No articles retrieved for query '%s'", query)
        return results

    # ------------------------------------------------------------------
    # LLM call with retry
    # ------------------------------------------------------------------
    def _call_llm(self, messages: list[dict], stream: bool = False):
        """Call Ollama with retry logic."""
        last_exc = None
        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                if stream:
                    return self.client.chat(self.model, messages=messages, stream=True)
                else:
                    return self.client.chat(self.model, messages=messages, stream=False)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Ollama call attempt %d/%d failed: %s",
                    attempt, RETRY_ATTEMPTS, exc
                )
                if attempt < RETRY_ATTEMPTS:
                    time.sleep(RETRY_DELAY)
                else:
                    raise last_exc

    # ------------------------------------------------------------------
    # Question answering (RAG)
    # ------------------------------------------------------------------
    def ask(
        self,
        query: str,
        stream: bool = False,
        retrieve_only: bool = False,
    ) -> dict:
        """
        Answer a question using RAG.

        Returns:
            dict with 'query', 'retrieved_articles', 'answer' (optional), 'citations' (optional).
        """
        retrieved_articles = self.retrieve(query)

        # Build the result skeleton
        result = {
            "query": query,
            "retrieved_articles": [
                {
                    "doc_id": art["doc_id"],
                    "title": art["title"],
                    "citation": art["citation"],
                    "score": art.get("score", 0.0),
                }
                for art in retrieved_articles
            ],
        }

        if retrieve_only:
            return result

        # Build prompt and call LLM (with retry)
        context = self.formatter.format_context(retrieved_articles)
        prompt = self.formatter.build_prompt(query, context)
        messages = [{"role": "user", "content": prompt}]

        try:
            if stream:
                def stream_wrapper():
                    response = self._call_llm(messages, stream=True)
                    for part in response:
                        yield part.message.content
                result["answer"] = stream_wrapper()
            else:
                response = self._call_llm(messages, stream=False)
                result["answer"] = response.message.content

            result["citations"] = [
                {"article": art["citation"], "title": art["title"], "doc_id": art["doc_id"]}
                for art in retrieved_articles
            ]
        except Exception as exc:
            logger.exception("LLM call failed after retries")
            result["answer"] = f"Error querying LLM: {str(exc)}"
            result["error"] = str(exc)

        return result

    def ask_streaming(self, query: str):
        """
        Answer with streaming response (generator).
        """
        retrieved_articles = self.retrieve(query)
        context = self.formatter.format_context(retrieved_articles)
        prompt = self.formatter.build_prompt(query, context)
        messages = [{"role": "user", "content": prompt}]

        try:
            response = self._call_llm(messages, stream=True)
            for part in response:
                yield part.message.content
        except Exception as exc:
            yield f"Error: {str(exc)}"


# Standalone demo (optional, unchanged)
def main():
    from ..core.engine_factory import EngineFactory

    engine = EngineFactory.from_artifacts(
        "data/output/flattened_nepal_constitution.json",
        "data/output"
    )
    workflow = RAGWorkflow(engine)

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