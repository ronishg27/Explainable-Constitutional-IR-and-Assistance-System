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
        self.lookup = {}
        for group in self.groups:
            group_words = set()
            for term in group:
                normalized = self._normalize(term)
                for word in normalized.split():
                    group_words.add(word)

            for word in group_words:
                if word not in self.lookup:
                    self.lookup[word] = set()
                self.lookup[word].update(group_words)

    def expand(self, tokens: list[str]) -> list[str]:
        if not tokens:
            return tokens

        seen = set()
        result = []

        for token in tokens:
            self._add_if_new(result, seen, token)

            if token in self.lookup:
                for synonym in self.lookup[token]:
                    self._add_if_new(result, seen, synonym)

        return result

    @staticmethod
    def _add_if_new(result: list[str], seen: set[str], item: str):
        if item not in seen:
            result.append(item)
            seen.add(item)
