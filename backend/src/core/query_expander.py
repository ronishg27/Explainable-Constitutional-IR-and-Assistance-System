import json


class QueryExpander:
    def __init__(self, synonyms_path: str):
        with open(synonyms_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.groups = data["groups"]
        self._build_lookup()

    @staticmethod
    def _normalize(term: str) -> str:
        text = term.lower().strip()
        return "".join(ch for ch in text if ch.isalnum() or ch.isspace())

    def _build_lookup(self):
        self.lookup: dict[str, dict[int, set[str]]] = {}
        self.multi_word_entries: dict[int, list[str]] = {}

        for group_idx, group in enumerate(self.groups):
            group_words = set()
            multi_terms = []

            for term in group:
                normalized = self._normalize(term)
                words = normalized.split()
                for word in words:
                    group_words.add(word)
                if len(words) > 1:
                    multi_terms.append(normalized)

            for word in group_words:
                self.lookup.setdefault(word, {})[group_idx] = group_words.copy()

            if multi_terms:
                self.multi_word_entries[group_idx] = multi_terms

    def expand(self, tokens: list[str], raw_query: str = "") -> list[str]:
        """Expand a list of tokens with their synonyms, preserving order and uniqueness."""
        if not tokens:
            return tokens

        seen = set()
        result = []
        raw_norm = self._normalize(raw_query)

        for token in tokens:
            self._add_if_new(result, seen, token)

            if token not in self.lookup:
                continue

            for group_idx, synonyms in self.lookup[token].items():
                if group_idx in self.multi_word_entries:
                    found = any(
                        phrase in raw_norm
                        for phrase in self.multi_word_entries[group_idx]
                    )
                    if not found:
                        continue

                for syn in synonyms:
                    self._add_if_new(result, seen, syn)

        return result

    @staticmethod
    def _add_if_new(result: list[str], seen: set[str], item: str):
        if item not in seen:
            result.append(item)
            seen.add(item)
