from ..constants.contraction_map import CONTRACTIONS_MAP
from ..constants.stopwords import STOPWORDS

_spacy_nlp = None

def get_spacy_pipeline():
    global _spacy_nlp

    if _spacy_nlp is None:
        try:
            import spacy
        except ImportError as exc:
            raise RuntimeError(
                "spaCy is required for spaCy-based preprocessing. "
                "Install it with: pip install spacy"
            ) from exc

        # Prefer a full English pipeline, but keep a lightweight fallback.
        try:
            _spacy_nlp = spacy.load("en_core_web_sm")
        except OSError:
            _spacy_nlp = spacy.blank("en")

    return _spacy_nlp


class TextProcessor:
    def __init__(self, use_lemmatization: bool = False, remove_stopwords: bool = False):
        self.use_lemmatization = use_lemmatization
        self.remove_stopwords = remove_stopwords
        self._nlp = None

    def _get_nlp(self):
        if self._nlp is None:
            self._nlp = get_spacy_pipeline()
        return self._nlp

    def _expand_contractions(self, text: str) -> str:
        if not text:
            return text

        for contraction, expansion in CONTRACTIONS_MAP.items():
            text = text.replace(contraction, expansion)
        return text

    def normalize_text(self, text: str) -> str:
        """Lowercase, expand contractions, keep only alphabetic characters."""
        text = text.lower().strip()
        text = self._expand_contractions(text)
        # Keep only letters and whitespace
        text = ''.join(ch for ch in text if ch.isalpha() or ch.isspace())
        return text

    def _filter_stopwords(self, tokens: list[str]) -> list[str]:
        """Remove stopwords from a list of tokens."""
        return [t for t in tokens if t not in STOPWORDS]

    def lemmatize_tokens(self, tokens: list[str]) -> list[str]:
        """Lemmatize a list of tokens (already normalised, not contracted)."""
        if not tokens:
            return []
        nlp = self._get_nlp()
        # Join with space – safe because tokens already alpha‑only, no punctuation
        doc = nlp(' '.join(tokens))
        lemmatized = []
        for token in doc:
            if token.is_space or token.is_punct:
                continue
            lemma = token.lemma_.strip().lower() if token.lemma_ else ""
            if lemma in {"", "-pron-"}:
                lemma = token.text.strip().lower()
            lemmatized.append(lemma)
        return lemmatized

    def process_text(self, text: str) -> list[str]:
        """Full pipeline: normalize, optionally lemmatize, optionally remove stopwords."""
        if not text:
            return []

        # Step 1 – Normalize (contractions, lowercase, alpha‑only)
        normalized_text = self.normalize_text(text)
        tokens = normalized_text.split()

        # Step 2 – Optional lemmatisation
        if self.use_lemmatization:
            tokens = self.lemmatize_tokens(tokens)

        # Step 3 – Optional stopword removal
        if self.remove_stopwords:
            tokens = self._filter_stopwords(tokens)

        return tokens