# src/core/proximity.py

import json
from pathlib import Path



class ProximityScorer:
    """Scores documents based on how close query term pairs appear in a positional index."""

    def __init__(self, positional_index: dict[str, dict[str, list[int]]]):
        self.index = positional_index

    # Pair generation
    @staticmethod
    def generate_adjacent_pairs(tokens: list[str]) -> list[tuple[str, str]]:
        """Sliding window of size 2 over consecutive tokens."""
        return [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]

    @staticmethod
    def generate_all_pairs(tokens: list[str]) -> list[tuple[str, str]]:
        """All unique unordered term pairs."""
        return [
            (tokens[i], tokens[j])
            for i in range(len(tokens))
            for j in range(i + 1, len(tokens))
        ]

    @staticmethod
    def generate_query_pairs(tokens: list[str]) -> list[tuple[str, str]]:
        """Heuristic: all pairs for short queries, adjacent for longer."""
        if len(tokens) <= 5:
            return ProximityScorer.generate_all_pairs(tokens)
        return ProximityScorer.generate_adjacent_pairs(tokens)

    # Distance helpers
    @staticmethod
    def _min_distance(pos1: list[int], pos2: list[int]) -> float:
        """Minimum absolute distance between any occurrence of two terms."""
        i = j = 0
        min_dist = float("inf")
        while i < len(pos1) and j < len(pos2):
            dist = abs(pos1[i] - pos2[j])
            if dist < min_dist:
                min_dist = dist
            if pos1[i] < pos2[j]:
                i += 1
            else:
                j += 1
        return (min_dist)

    @staticmethod
    def _min_ordered_distance(pos1: list[int], pos2: list[int]) -> float:
        """Minimum distance where term1 occurs before term2."""
        i = j = 0
        min_dist = float("inf")
        while i < len(pos1) and j < len(pos2):
            if pos1[i] < pos2[j]:
                dist = pos2[j] - pos1[i]
                if dist < min_dist:
                    min_dist = dist
                i += 1
            else:
                j += 1
        return (min_dist)

    # Scoring
    def score(
        self,
        doc_id: str,
        pairs: list[tuple[str, str]],
        max_window: int = 30,
        ordered: bool = True,
    ) -> float:
        """
        Average quadratic inverse proximity score.
        Score per valid pair = 1/(distance+1)^2, capped at max_window.
        Returns 0.0 if no valid pairs.
        """
        distance_func = self._min_ordered_distance if ordered else self._min_distance

        total = 0.0
        valid = 0

        for term1, term2 in pairs:
            if term1 == term2:
                continue

            postings1 = self.index.get(term1, {})
            postings2 = self.index.get(term2, {})
            if doc_id not in postings1 or doc_id not in postings2:
                continue

            positions1 = postings1[doc_id]
            positions2 = postings2[doc_id]
            d = distance_func(positions1, positions2)

            if d > max_window:
                continue

            total += 1.0 / ((d + 1) ** 2)
            valid += 1

        return total / valid if valid else 0.0

    # load/save helpers
    @staticmethod
    def load_index(path: Path) -> dict[str, dict[str, list[int]]]:
        """Load a positional index from a JSON file."""
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    
    def save_index(self, path: Path) -> None:
        """Save the positional index to a JSON file."""
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
    

