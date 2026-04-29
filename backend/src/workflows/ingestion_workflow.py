from pathlib import Path
from typing import Optional

from ..core.bm25 import BM25, load_documents
from ..core.preprocessing import NLP


class IngestionWorkflow:
    """Handles document loading and index-building steps."""

    def __init__(self, documents_path: Optional[str] = None):
        self.documents_path = self._resolve_documents_path(documents_path)

    @staticmethod
    def _resolve_documents_path(documents_path: Optional[str]) -> Path:
        if documents_path is not None:
            return Path(documents_path)

        root = Path(__file__).resolve().parents[2]
        return root / "data" / "output" / "flattened_nepal_constitution.json"

    def load_documents(self) -> list[dict]:
        return load_documents(str(self.documents_path))

    def build_retrieval_state(self) -> tuple[list[dict], BM25]:
        documents = self.load_documents()
        return documents, BM25(documents)

    @staticmethod
    def build_inverted_index(documents: list[dict]) -> dict:
        """Build an inverted index using shared tokenization rules."""
        index: dict = {}

        for doc in documents:
            doc_id = doc["doc_id"]
            tokens = NLP.tokenize(doc["text"])

            for token in tokens:
                if token not in index:
                    index[token] = {}
                index[token][doc_id] = index[token].get(doc_id, 0) + 1

        return index


    @staticmethod
    def build_positional_inverted_index(documents: list[dict]) -> dict:
        """Build an n-gram phrase index using shared tokenization rules."""
        index: dict = {}

        for doc in documents:
            doc_id = doc["doc_id"]
            tokens = NLP.tokenize(doc["text"], remove_stopwords=False)
            
            for token in tokens:
                if token not in index:
                    index[token] = {}
                if doc_id not in index[token]:
                    index[token][doc_id] = []
                index[token][doc_id].append(tokens.index(token))

        return index