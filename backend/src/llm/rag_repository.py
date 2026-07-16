import logging
import os
import time
from typing import Any, Optional

from ollama import Client

from ..workflows.retrieval_workflow import RetrievalWorkflow

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemma3:1b"
RETRY_ATTEMPTS = 3
RETRY_DELAY = 0.5


class RAGRepository:
    """Data-access layer for the LLM module.

    Owns the Ollama client, connectivity checks, LLM calls with retry,
    and delegates retrieval to RetrievalWorkflow.
    """

    def __init__(
        self,
        retrieval_workflow: RetrievalWorkflow,
        model: Optional[str] = None,
        ollama_host: Optional[str] = None,
    ):
        self.retrieval = retrieval_workflow
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)

        host = ollama_host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        api_key = os.environ.get("OLLAMA_API_KEY") or ""
        headers = {"Authorization": f"Bearer {api_key.strip()}"} if api_key.strip() else None
        self.client = Client(host=host, headers=headers)

        self._ollama_available: Optional[bool] = None
        self._available_models: list[str] = []
        self._connection_status: str = "Not checked yet."

        self._article_lookup: dict[str, dict] = {}
        self._clause_structure: dict[str, dict] = {}
        self._build_article_lookup()

    # ------------------------------------------------------------------
    # Article-level promotion
    # ------------------------------------------------------------------
    def _build_article_lookup(self) -> None:
        """Group all documents by article_no and pre-build full article texts.

        For articles that already have an article-level Document (e.g. articles
        with lettered sub_clauses) we use its text directly.  For articles
        stored only as individual clause/sub-clause Documents (e.g. numbered
        clauses), we concatenate all constituent texts into one full article.
        """
        if not hasattr(self.retrieval, "engine") or not hasattr(self.retrieval.engine, "documents"):
            logger.warning("Retrieval engine documents not available; article lookup will be empty.")
            return

        from collections import defaultdict

        groups: dict[str, dict] = defaultdict(lambda: {
            "article_doc": None,
            "clause_docs": [],
            "title": "",
            "citation": "",
            "part_no": "",
        })

        for doc in self.retrieval.engine.documents:
            key = doc.article_no
            if doc.level == "article":
                groups[key]["article_doc"] = doc
                groups[key]["title"] = doc.title
                groups[key]["citation"] = doc.citation
                groups[key]["part_no"] = doc.part_no
            elif doc.level in ("clause", "sub-clause"):
                groups[key]["clause_docs"].append(doc)
                if not groups[key]["title"]:
                    groups[key]["title"] = doc.title
                    groups[key]["part_no"] = doc.part_no

        self._article_lookup = {}
        for article_no, data in groups.items():
            if data["article_doc"] is not None:
                text = data["article_doc"].text
                citation = data["citation"]
            else:
                texts = [d.text for d in data["clause_docs"]]
                text = "\n---\n".join(texts)
                citation = f"Part {data['part_no']}, Article {article_no}"

            self._article_lookup[article_no] = {
                "article_no": article_no,
                "part_no": data["part_no"],
                "title": data["title"],
                "citation": citation,
                "text": text,
            }

        self._clause_structure = {}
        for article_no, data in groups.items():
            if data["clause_docs"]:
                clauses = {}
                for doc in data["clause_docs"]:
                    cn = doc.clause_no
                    if cn is not None:
                        clauses[cn] = {"text": doc.text, "clause_no": cn}
                if clauses:
                    self._clause_structure[article_no] = {
                        "title": data["title"],
                        "clauses": clauses,
                    }

    def promote_to_articles(self, results: list[dict]) -> list[dict]:
        """Convert clause/sub-clause results to full article results, deduplicating by article_no.

        Results are assumed sorted by descending score; the first occurrence
        of each article determines its final score.
        """
        if not self._article_lookup:
            return results

        matched_clauses_per_article: dict[str, set] = {}
        for result in results:
            an = result["article_no"]
            if an not in matched_clauses_per_article:
                matched_clauses_per_article[an] = set()
            cn = result.get("clause_no")
            if cn is not None:
                matched_clauses_per_article[an].add(cn)

        seen: set[str] = set()
        promoted: list[dict] = []

        for result in results:
            article_no = result["article_no"]
            if article_no in seen:
                continue
            seen.add(article_no)

            article = self._article_lookup.get(article_no)
            if article is None:
                promoted.append(result)
                continue

            promoted.append({
                "doc_id": str(article["article_no"]),
                "part_no": article["part_no"],
                "article_no": article["article_no"],
                "title": article["title"],
                "text": article["text"],
                "citation": article["citation"],
                "level": "article",
                "score": result.get("score", 0.0),
                "bm25_score": result.get("bm25_score", 0.0),
                "proximity_score": result.get("proximity_score", 0.0),
                "title_match_count": result.get("title_match_count", 0),
                "matched_terms": result.get("matched_terms", []),
                "exact_matched_terms": result.get("exact_matched_terms", []),
                "boost_multiplier": result.get("boost_multiplier", 1.0),
                "matched_clauses": sorted(matched_clauses_per_article.get(article_no, set())),
            })

        return promoted

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        boost_rules: Optional[dict] = None,
    ) -> list[dict]:
        """Delegate to RetrievalWorkflow and return ranked articles."""
        return self.retrieval.retrieve(query, top_k=top_k, boost_rules=boost_rules)

    # ------------------------------------------------------------------
    # Context truncation
    # ------------------------------------------------------------------
    def build_truncated_text(self, article: dict) -> str:
        """Return article text truncated to header + matched clauses only.

        For single-block articles (no clause structure) or articles where
        no clause-level match was found, returns the full text as-is.
        """
        article_no = article["article_no"]
        structure = self._clause_structure.get(article_no)
        if not structure or not structure.get("clauses"):
            return article["text"]

        matched = article.get("matched_clauses", [])
        if not matched:
            return article["text"]

        header = f"Part {article['part_no']} Article {article_no}"
        title_line = structure["title"]

        clause_texts = []
        for cn in sorted(matched):
            clause = structure["clauses"].get(cn)
            if clause:
                clause_texts.append(clause["text"])

        if not clause_texts:
            return article["text"]

        parts = [f"{header}\n\n{title_line}"]
        parts.extend(clause_texts)
        return "\n---\n".join(parts)

    # ------------------------------------------------------------------
    # Ollama connectivity (with caching)
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_model_names(models_response: Any) -> list[str]:
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
        if self._ollama_available is None:
            logger.info("Performing initial Ollama connectivity check...")
            self._ollama_available, self._connection_status = self._perform_ollama_check()
            if self._ollama_available:
                logger.info(self._connection_status)
            else:
                logger.warning(self._connection_status)

    def check_ollama_connection(self) -> tuple[bool, str]:
        """Return cached or fresh connectivity status."""
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
    # LLM call with retry
    # ------------------------------------------------------------------
    def call_llm(self, messages: list[dict], stream: bool = False) -> Any:
        """Call Ollama with retry logic."""
        last_exc = None
        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                if stream:
                    return self.client.chat(self.model, messages=messages, stream=True,
                                            keep_alive="30m", options={
                                                "num_ctx": 4096,})
                else:
                    return self.client.chat(self.model, messages=messages, stream=False, keep_alive="30m", options={
                        "num_ctx": 4096,})
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Ollama call attempt %d/%d failed: %s",
                    attempt, RETRY_ATTEMPTS, exc,
                )
                if attempt < RETRY_ATTEMPTS:
                    time.sleep(RETRY_DELAY)
        raise last_exc
