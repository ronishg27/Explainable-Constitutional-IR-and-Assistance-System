# src/core/search_engine.py
"""
Constitution search engine combining BM25, title boost, and proximity scoring.

The central retrieval pipeline:
    1. Pre‑process query for BM25 (lemmatised, stopwords removed)
       and for proximity (raw tokens, stopwords kept).
    2. Candidate generation from the BM25 term‑frequency index.
    3. Score each candidate document by:
         BM25           – term importance and saturation
         + title_boost  – additional weight for query terms in the article title
         + proximity    – how close query term pairs appear in the document
    4. Return top‑k documents sorted by combined score.

Constants (tunable):
    DEFAULT_PROXIMITY_WEIGHT = 1.0
    DEFAULT_TITLE_BOOST      = 5.0
    DEFAULT_MAX_WINDOW       = 30
"""

from typing import Optional
from .bm25_scorer import BM25Scorer
from .proximity import ProximityScorer
from .query_expander import QueryExpander
from .text_processor import TextProcessor
from .document import Document

# -------------------------------------------------------------------
# Tunable constants
# -------------------------------------------------------------------
DEFAULT_PROXIMITY_WEIGHT = 1.0   # factor for proximity score vs. BM25
DEFAULT_TITLE_BOOST = 5.0        # bonus for matching a query token in the article title
DEFAULT_MAX_WINDOW = 30          # maximum token distance for proximity pairs


class SearchEngine:
    """
    Retrieval pipeline for constitution articles.

    Usage:
        engine = EngineFactory.from_artifacts(docs_path, index_dir)
        results = engine.search(query, top_k=5)
    """

    def __init__(
        self,
        bm25_scorer: BM25Scorer,
        proximity_scorer: ProximityScorer,
        bm25_processor: TextProcessor,       # use_lemmatization=True, remove_stopwords=True
        proximity_processor: TextProcessor,   # use_lemmatization=False, remove_stopwords=False
        documents: list[Document],
        proximity_weight: float = DEFAULT_PROXIMITY_WEIGHT,
        title_boost: float = DEFAULT_TITLE_BOOST,
        default_top_k: int = 5,
        max_window: int = DEFAULT_MAX_WINDOW,
        synonym_expander: Optional[QueryExpander] = None,
    ):
        """
        All dependencies are injected so the engine can be constructed
        from pre‑built indexes or built in‑memory.
        """
        self.bm25_scorer = bm25_scorer
        self.proximity_scorer = proximity_scorer
        self.bm25_processor = bm25_processor
        self.proximity_processor = proximity_processor
        self.synonym_expander = synonym_expander
        self.documents = documents
        self.proximity_weight = proximity_weight
        self.title_boost = title_boost
        self.default_top_k = default_top_k
        self.max_window = max_window

        # Pre‑tokenize titles once for fast title‑boost lookups
        self.title_tokens: dict[str, list[str]] = {}
        for doc in documents:
            self.title_tokens[doc.doc_id] = self.bm25_processor.process_text(doc.title)

    # Public API
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        proximity_weight: Optional[float] = None,
        title_boost: Optional[float] = None,
    ) -> list[dict]:
        """
        Run the full retrieval pipeline for a user query.

        Returns:
            List of dicts with keys: doc_id, part_no, article_no, title,
            text, citation, level, clause_no, subclause_id, score.
        """
        top_k = top_k or self.default_top_k
        proximity_weight = proximity_weight if proximity_weight is not None else self.proximity_weight
        title_boost = title_boost if title_boost is not None else self.title_boost

        # 1. Prepare query tokens
        base_tokens = self.bm25_processor.process_text(query)
        if not base_tokens:
            return []

        bm25_tokens = base_tokens[:]
        if self.synonym_expander:
            bm25_tokens = self.synonym_expander.expand(bm25_tokens, raw_query=query)

        raw_tokens = self._prepare_proximity_query(query)
        query_pairs = ProximityScorer.generate_query_pairs(raw_tokens)

        # 2. Generate candidate set from BM25 index
        candidates = self._generate_candidates(bm25_tokens)
        if not candidates:
            return []

        # 3. Score all candidates
        scored = []
        for doc in self.documents:
            if doc.doc_id not in candidates:
                continue
            result = self._score_document(
                doc, bm25_tokens, base_tokens, query_pairs, title_boost, proximity_weight
            )
            if result[0] > 0:
                scored.append(result)

        # 4. Sort descending and cut top‑k
        scored.sort(key=lambda x: x[0], reverse=True)
        return self._format_results(scored[:top_k])

    # Private pipeline steps
    def _prepare_proximity_query(self, query: str) -> list[str]:
        """Tokenize without lemmatisation, keeping stopwords (for exact proximity matching)."""
        return self.proximity_processor.process_text(query)

    def _generate_candidates(self, bm25_tokens: list[str]) -> set[str]:
        """Collect document IDs that contain at least one query term (BM25 index)."""
        candidates: set[str] = set()
        for token in bm25_tokens:
            if token in self.bm25_scorer.tf_index:
                candidates.update(self.bm25_scorer.tf_index[token].keys())
        return candidates

    def _score_document(
        self,
        doc: Document,
        bm25_tokens: list[str],
        original_tokens: list[str],
        query_pairs: list[tuple[str, str]],
        title_boost: float,
        proximity_weight: float,
    ) -> tuple[float, float, float, int, Document, list[str], list[str]]:
        """
        Compute combined score for a single document.

        Score = BM25 + (title_matches * title_boost) + proximity_weight * proximity_score

        Returns:
            (final_score, bm25_score, proximity_score, title_match_count, doc, matched_terms, exact_matched_terms)
        """
        bm25 = self.bm25_scorer.score(bm25_tokens, doc.doc_id)
        if bm25 == 0.0:
            return 0.0, 0.0, 0.0, 0, doc, [], []

        # Query terms that matched in BM25 (for frontend highlighting)
        matched = self.bm25_scorer.matched_terms(bm25_tokens, doc.doc_id)
        exact_matched = self.bm25_scorer.matched_terms(original_tokens, doc.doc_id)

        # Title boost: extra weight for query terms appearing in the title
        title_match_count = len(set(bm25_tokens) & set(self.title_tokens[doc.doc_id]))
        boosted_bm25 = bm25 + title_match_count * title_boost

        # Proximity score
        prox = self.proximity_scorer.score(
            doc.doc_id,
            query_pairs,
            max_window=self.max_window,
            ordered=True,
        )

        return boosted_bm25 + proximity_weight * prox, bm25, prox, title_match_count, doc, matched, exact_matched

    def _format_results(self, scored_docs: list[tuple]) -> list[dict]:
        """Convert scored Document objects to dictionaries for API/CLI output."""
        results = []
        for entry in scored_docs:
            final_score, bm25_score, prox_score, title_match_count, doc, matched, exact_matched = entry
            results.append({
                "doc_id": doc.doc_id,
                "part_no": doc.part_no,
                "article_no": doc.article_no,
                "title": doc.title,
                "text": doc.text,
                "citation": doc.citation,
                "level": doc.level,
                "clause_no": doc.clause_no,
                "subclause_id": doc.subclause_id,
                "score": final_score,
                "bm25_score": bm25_score,
                "proximity_score": prox_score,
                "title_match_count": title_match_count,
                "boost": doc.boost,
                "matched_terms": matched,
                "exact_matched_terms": exact_matched,
            })
        return results