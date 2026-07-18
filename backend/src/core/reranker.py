import math


class Reranker:
    """Algorithmic reranking: RRF signal fusion → MMR diversity → rule-based boost.

    Uses no ML/embeddings. All operations are concrete:
      - RRF (Reciprocal Rank Fusion) combines BM25, proximity, and title-match ranks.
      - MMR (Maximal Marginal Relevance) uses BM25 term-frequency cosine similarity.
      - Rule-based boost applies configurable multipliers (part, level, doc.boost).
    """

    def __init__(
        self,
        tf_index: dict[str, dict[str, int]],
        rrf_k: int = 60,
        mmr_lambda: float = 0.5,
    ):
        self.tf_index = tf_index
        self.rrf_k = rrf_k
        self.mmr_lambda = mmr_lambda
        self._vector_cache: dict[str, dict[str, int]] = {}

    # ------------------------------------------------------------------
    # BM25 term-frequency vector helpers (for cosine similarity)
    # ------------------------------------------------------------------
    def _get_tf_vector(self, doc_id: str) -> dict[str, int]:
        """Build or retrieve a cached sparse tf vector for a document."""
        if doc_id not in self._vector_cache:
            vector: dict[str, int] = {}
            for term, postings in self.tf_index.items():
                tf = postings.get(doc_id, 0)
                if tf > 0:
                    vector[term] = tf
            self._vector_cache[doc_id] = vector
        return self._vector_cache[doc_id]

    @staticmethod
    def _cosine_similarity(vec_a: dict[str, int], vec_b: dict[str, int]) -> float:
        """Cosine similarity between two sparse term-frequency vectors."""
        intersection = set(vec_a.keys()) & set(vec_b.keys())
        if not intersection:
            return 0.0
        dot = sum(vec_a[t] * vec_b[t] for t in intersection)
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    # ------------------------------------------------------------------
    # Stage 1: Reciprocal Rank Fusion
    # ------------------------------------------------------------------
    def _rrf_fuse(self, results: list[dict]) -> list[dict]:
        """Fuse BM25, proximity, and title-match ranks via RRF."""
        if not results:
            return results

        k = self.rrf_k
        n = len(results)

        # Rank documents by each signal (descending score → ascending rank)
        def _ranked(signal_key: str):
            return [
                (i + 1, r["doc_id"])
                for i, r in enumerate(
                    sorted(results, key=lambda x: x.get(signal_key, 0), reverse=True)
                )
            ]

        bm25_ranks = dict(_ranked("bm25_score"))
        prox_ranks = dict(_ranked("proximity_score"))
        title_ranks = dict(_ranked("title_match_count"))

        for result in results:
            doc_id = result["doc_id"]
            rrf = 0.0
            rrf += 1.0 / (k + bm25_ranks.get(doc_id, n))
            rrf += 1.0 / (k + prox_ranks.get(doc_id, n))
            rrf += 1.0 / (k + title_ranks.get(doc_id, n))
            result["rrf_score"] = rrf

        results.sort(key=lambda x: x["rrf_score"], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Stage 2: MMR diversity rerank
    # ------------------------------------------------------------------
    def _mmr_diversify(self, results: list[dict]) -> list[dict]:
        """Reorder results to balance score and diversity via MMR."""
        if len(results) <= 1:
            return results

        selected: list[dict] = []
        candidates = list(results)

        # First pick: highest RRF score
        selected.append(candidates.pop(0))

        while candidates:
            best_idx = 0
            best_mmr = -float("inf")
            vec_candidates = [
                self._get_tf_vector(c["doc_id"]) for c in candidates
            ]
            vec_selected = [
                self._get_tf_vector(s["doc_id"]) for s in selected
            ]

            for i, cand in enumerate(candidates):
                score = cand.get("rrf_score", cand.get("score", 0.0))

                max_sim = 0.0
                for v_sel in vec_selected:
                    sim = self._cosine_similarity(vec_candidates[i], v_sel)
                    if sim > max_sim:
                        max_sim = sim

                mmr = self.mmr_lambda * score - (1.0 - self.mmr_lambda) * max_sim
                if mmr > best_mmr:
                    best_mmr = mmr
                    best_idx = i

            selected.append(candidates.pop(best_idx))

        return selected

    # ------------------------------------------------------------------
    # Stage 3: Rule-based boost
    # ------------------------------------------------------------------
    @staticmethod
    def _apply_boost(results: list[dict], boost_rules: dict | None = None) -> list[dict]:
        """Apply per-document boost field + part/level rule multipliers.

        Multiplies each result's ``score`` by the applicable boost multipliers.
        Order from the previous pipeline stage (MMR) is preserved.
        """
        part_rules = (boost_rules or {}).get("part_boost", {})
        level_rules = (boost_rules or {}).get(
            "level_boost",
            {"part": 1.0, "article": 0.98, "clause": 0.95, "subclause": 0.90},
        )

        for result in results:
            boost = result.get("boost", 1.0)
            part_no = str(result.get("part_no", ""))
            level = result.get("level", "")
            score = result.get("score", 0.0)

            multiplier = boost
            if part_no in part_rules:
                multiplier *= part_rules[part_no]
            if level in level_rules:
                multiplier *= level_rules[level]

            result["score"] = score * multiplier
            result["boost_multiplier"] = multiplier

        return results

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def rerank(
        self,
        results: list[dict],
        top_k: int = 8,
        boost_rules: dict | None = None,
    ) -> list[dict]:
        """Run the full reranking pipeline and return top-k results.

        Pipeline: RRF fusion → sort → MMR diversity → rule-based boost → top-k cut.
        """
        if not results:
            return results

        res = self._rrf_fuse(results)
        res = self._mmr_diversify(res)
        res = self._apply_boost(res, boost_rules)
        return res[:top_k]
