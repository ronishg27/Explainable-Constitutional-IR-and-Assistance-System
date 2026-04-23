import re
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from constants.stopwords import STOPWORDS

_spacy_nlp = None


def _get_spacy_pipeline():
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

class NLP:
    def __init__(self):
        pass
        # root_dir = Path(__file__).resolve().parents[2]
        # lemma_path = root_dir / "data" / "lemma_dict_v3.json"
        # with lemma_path.open("r", encoding="utf-8") as f:
        #     self.lemma_dict = json.load(f)


    @staticmethod
    def preprocess(text):
        """Preprocesses the input text by normalizing, tokenizing, and removing stopwords."""
        normalized_text = NLP.normalize(text)
        tokens = NLP.tokenize(normalized_text)
        filtered_tokens = NLP.remove_stopwords(tokens)
        lemmatized_tokens = NLP.lemmatize(filtered_tokens)
        return lemmatized_tokens

    @staticmethod
    def normalize(text):
        """Normalizes the input text by converting it to lowercase and removing punctuation."""
        if not text:
            return ""

        normalized_text = text.lower()
        normalized_text = re.sub(r'[^\w\s]', ' ', normalized_text)
        return normalized_text


    @staticmethod
    def tokenize(text):
        """Tokenizes the input text into a list of tokens."""
        if not text:
            return []
        
        tokens = text.split()
        return tokens
    
    @staticmethod
    def remove_stopwords(tokens):
        """Removes stopwords from the list of tokens."""
        return [token for token in tokens if token not in STOPWORDS]
    

    @staticmethod
    def lemmatize(tokens):
        """Lemmatizes the input tokens to their base forms."""
        return [NLP.lemma_dict.get(token, token) for token in tokens]

    @staticmethod
    def expand_query(query):
        """Expands the input query by adding synonyms or related terms."""
        if not query:
            return ""

        nlp = _get_spacy_pipeline()
        doc = nlp(query)

        expanded_terms = []
        seen = set()

        for token in doc:
            if token.is_space or token.is_punct:
                continue

            raw = token.text.strip().lower()
            lemma = token.lemma_.strip().lower() if token.lemma_ else ""

            if lemma in {"", "-pron-"}:
                lemma = raw

            for term in (raw, lemma):
                if not term or term in STOPWORDS or term in seen:
                    continue
                seen.add(term)
                expanded_terms.append(term)

        return " ".join(expanded_terms)

    @staticmethod
    def lemmatize_text(text):
        """Lemmatizes the input text using spaCy."""
        if not text:
            return []

        nlp = _get_spacy_pipeline()
        doc = nlp(text)

        lemmatized_tokens = []
        for token in doc:
            if token.is_space or token.is_punct:
                continue

            lemma = token.lemma_.strip().lower() if token.lemma_ else ""
            if lemma in {"", "-pron-"}:
                lemma = token.text.strip().lower()

            if lemma and lemma not in STOPWORDS:
                lemmatized_tokens.append(lemma)

        return lemmatized_tokens


if __name__ == "__main__":
    nlp = NLP()
    sample_text = "The quick brown foxes were jumping over the lazy dogs. They've been doing this for years! Isn't it amazing?  "
    # processed_tokens = nlp.preprocess(sample_text)
    processed_tokens = nlp.lemmatize_text(sample_text)
    print(processed_tokens)
    

