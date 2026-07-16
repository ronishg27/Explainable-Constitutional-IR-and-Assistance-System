# src/core/engine_factory.py
"""
Factory that assembles a SearchEngine from pre‑built disk artifacts.

Usage:
    engine = EngineFactory.from_artifacts(
        "data/output/flattened_nepal_constitution.json",
        "data/output"
    )
    results = engine.search("fundamental rights")
"""

import json
import logging
from pathlib import Path
from .document import Document
from .query_expander import QueryExpander
from .text_processor import TextProcessor
from .bm25_scorer import BM25Scorer
from .proximity import ProximityScorer
from .search_engine import SearchEngine

logger = logging.getLogger(__name__)


class EngineFactory:
    """Constructs a ready‑to‑use SearchEngine from saved indexes."""

    @staticmethod
    def from_artifacts(
        documents_path: str,
        index_dir: str,
        proximity_weight: float = 1.0,
        title_boost: float = 5.0,
        synonyms_path: str | None = None,
    ) -> SearchEngine:
        """
        Load flattened documents and pre‑computed indexes from disk.

        Args:
            documents_path: Path to flattened_nepal_constitution.json
            index_dir: Directory containing tf_index.json, pos_index.json, doc_stats.json
            proximity_weight: How much proximity score contributes (default 1.0)
            title_boost: Bonus per matching title token (default 5.0)

        Returns:
            A fully initialised SearchEngine, ready for search() calls.

        Raises:
            FileNotFoundError: If any required artifact is missing.
            json.JSONDecodeError: If any artifact is malformed.
        """
        try:
            with open(documents_path, "r", encoding="utf-8") as f:
                raw_docs = json.load(f)
        except FileNotFoundError:
            logger.error("Documents file not found: %s", documents_path)
            raise
        except json.JSONDecodeError:
            logger.error("Documents file is not valid JSON: %s", documents_path)
            raise

        documents = [Document(**item) for item in raw_docs]

        base = Path(index_dir)
        index_files = {
            "tf_index.json": None,
            "pos_index.json": None,
            "doc_stats.json": None,
        }
        for name in index_files:
            path = base / name
            try:
                with open(path, "r", encoding="utf-8") as f:
                    index_files[name] = json.load(f)
            except FileNotFoundError:
                logger.error("Index file not found: %s", path)
                raise
            except json.JSONDecodeError:
                logger.error("Index file is not valid JSON: %s", path)
                raise

        tf_index = index_files["tf_index.json"]
        pos_index = index_files["pos_index.json"]
        stats = index_files["doc_stats.json"]

        doc_lengths = stats["doc_lengths"]
        avgdl = stats["avgdl"]

        bm25_proc = TextProcessor(use_lemmatization=True, remove_stopwords=True)
        prox_proc = TextProcessor(use_lemmatization=False, remove_stopwords=False)

        synonym_expander = None
        if synonyms_path:
            synonym_expander = QueryExpander(synonyms_path)

        bm25_scorer = BM25Scorer(tf_index, doc_lengths, avgdl)
        prox_scorer = ProximityScorer(pos_index)

        return SearchEngine(
            bm25_scorer,
            prox_scorer,
            bm25_proc,
            prox_proc,
            documents,
            proximity_weight=proximity_weight,
            title_boost=title_boost,
            synonym_expander=synonym_expander,
        )