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
from pathlib import Path
from .document import Document
from .text_processor import TextProcessor
from .bm25_scorer import BM25Scorer
from .proximity import ProximityScorer
from .search_engine import SearchEngine


class EngineFactory:
    """Constructs a ready‑to‑use SearchEngine from saved indexes."""

    @staticmethod
    def from_artifacts(
        documents_path: str,
        index_dir: str,
        proximity_weight: float = 1.0,
        title_boost: float = 5.0,
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
        """
        # 1. Load documents as Document objects
        with open(documents_path, "r", encoding="utf-8") as f:
            raw_docs = json.load(f)
        documents = [Document(**item) for item in raw_docs]

        # 2. Load indexes
        base = Path(index_dir)
        with open(base / "tf_index.json", "r", encoding="utf-8") as f:
            tf_index = json.load(f)
        with open(base / "pos_index.json", "r", encoding="utf-8") as f:
            pos_index = json.load(f)
        with open(base / "doc_stats.json", "r", encoding="utf-8") as f:
            stats = json.load(f)

        doc_lengths = stats["doc_lengths"]
        avgdl = stats["avgdl"]

        # 3. Create the two processors
        bm25_proc = TextProcessor(use_lemmatization=True, remove_stopwords=True)
        prox_proc = TextProcessor(use_lemmatization=False, remove_stopwords=False)

        # 4. Assemble engine
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
        )