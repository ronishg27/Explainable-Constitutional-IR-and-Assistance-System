# src/workflows/ingestion_workflow.py
"""
Offline ingestion workflow: loads documents, builds indexes, saves to disk.

Usage:
    from preprocessing_scripts.build_index import main
    main()
"""

import json
from pathlib import Path
import dataclasses
from ..core.document import Document
from ..core.text_processor import TextProcessor
from ..core.index_builder import IndexBuilder


class IngestionWorkflow:
    """Builds and persists the three index files needed by SearchEngine."""

    def __init__(self, documents_path: str):
        self.doc_path = Path(documents_path)
        # Two processors: one for BM25 (lemmatised, no stopwords), one for proximity (raw)
        self.bm25_proc = TextProcessor(use_lemmatization=True, remove_stopwords=True)
        self.prox_proc = TextProcessor(use_lemmatization=False, remove_stopwords=False)

    # -----------------------------------------------------------------
    # Document loading
    # -----------------------------------------------------------------
    def load_documents(self) -> list[Document]:
        """Load flattened constitution JSON as Document objects."""
        with open(self.doc_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            
        allowed_fields = {f.name for f in dataclasses.fields(Document)}
        documents = []
        for item in raw:
            clean_item = {k: v for k, v in item.items() if k in allowed_fields}
            documents.append(Document(**clean_item))
        return documents

    # -----------------------------------------------------------------
    # Index building
    # -----------------------------------------------------------------
    def build_indexes(self) -> tuple[dict, dict, dict]:
        """
        Build tf_index, positional_index, and doc_stats.

        Returns:
            tf_index, pos_index, doc_stats (dict with 'doc_lengths' and 'avgdl')
        """
        docs = self.load_documents()
        builder = IndexBuilder(self.bm25_proc, self.prox_proc)
        tf_index = builder.build_tf_index(docs)
        pos_index = builder.build_positional_index(docs)
        doc_lengths, avgdl = builder.compute_doc_stats(docs)
        doc_stats = {"doc_lengths": doc_lengths, "avgdl": avgdl}
        return tf_index, pos_index, doc_stats

    def save_indexes(self, output_dir: str = "data/output") -> None:
        """Build indexes and persist them to JSON files."""
        tf_index, pos_index, doc_stats = self.build_indexes()
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        with open(out / "tf_index.json", "w", encoding="utf-8") as f:
            json.dump(tf_index, f, ensure_ascii=False, indent=2)
        with open(out / "pos_index.json", "w", encoding="utf-8") as f:
            json.dump(pos_index, f, ensure_ascii=False, indent=2)
        with open(out / "doc_stats.json", "w", encoding="utf-8") as f:
            json.dump(doc_stats, f, ensure_ascii=False, indent=2)