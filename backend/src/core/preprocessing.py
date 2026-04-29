import re

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

class NLP:
    CONTRACTIONS_MAP = {
        "ain't": "am not",
        "aren't": "are not",
        "can't": "cannot",
        "can't've": "cannot have",
        "could've": "could have",
        "couldn't": "could not",
        "didn't": "did not",
        "doesn't": "does not",
        "don't": "do not",
        "hadn't": "had not",
        "hasn't": "has not",
        "haven't": "have not",
        "he'd": "he would",
        "he'll": "he will",
        "he's": "he is",
        "how'd": "how did",
        "how'll": "how will",
        "how's": "how is",
        "i'd": "i would",
        "i'll": "i will",
        "i'm": "i am",
        "i've": "i have",
        "isn't": "is not",
        "it'd": "it would",
        "it'll": "it will",
        "it's": "it is",
        "let's": "let us",
        "shouldn't": "should not",
        "that'd": "that would",
        "that's": "that is",
        "there'd": "there would",
        "there's": "there is",
        "they'd": "they would",
        "they'll": "they will",
        "they're": "they are",
        "they've": "they have",
        "wasn't": "was not",
        "we'd": "we would",
        "we'll": "we will",
        "we're": "we are",
        "we've": "we have",
        "weren't": "were not",
        "what's": "what is",
        "where'd": "where did",
        "where's": "where is",
        "who'd": "who would",
        "who'll": "who will",
        "who're": "who are",
        "who's": "who is",
        "won't": "will not",
        "wouldn't": "would not",
        "you'd": "you would",
        "you'll": "you will",
        "you're": "you are",
        "you've": "you have",
    }

    def __init__(self):
        pass



    @staticmethod
    def expand_contractions(text: str) -> str:
        """Expands contractions in text (e.g., "don't" -> "do not")."""
        if not text:
            return ""

        pattern = re.compile(
            r"\b" + "|".join(re.escape(key) for key in NLP.CONTRACTIONS_MAP) + r"\b",
            re.IGNORECASE,
        )

        def replace_contraction(match):
            contraction = match.group(0).lower()
            return NLP.CONTRACTIONS_MAP.get(contraction, contraction)

        return pattern.sub(replace_contraction, text)

    @staticmethod
    def preprocess(text):
        """Preprocesses the input text by normalizing, tokenizing, and removing stopwords."""
        tokens = NLP.tokenize(text)
        lemmatized_tokens = NLP.lemmatize(tokens)
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
    def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
        """Tokenizes text into lowercase word tokens, removing stopwords and non-letters."""
        if not text:
            return []

        normalized_text = NLP.normalize(text)
        tokens = normalized_text.split()
        if remove_stopwords:
            tokens = NLP.remove_stopwords(tokens)
        else:
            tokens = [ token for token in tokens if token.isalpha() ]
        return tokens

    @staticmethod
    def remove_stopwords(tokens: list[str]) -> list[str]:
        """Removes stopwords from the list of tokens."""
        return [ token
                for token in tokens 
                if token.isalpha() and token not in STOPWORDS
                    ]
    

    @staticmethod
    def lemmatize(tokens: list[str]) -> list[str]:
        """Lemmatizes the input tokens using spaCy."""
        return NLP.lemmatize_text(" ".join(tokens))

    @staticmethod
    def expand_query(query: str) -> str:
        """Expands the input query by adding synonyms or related terms."""
        if not query:
            return ""

        query = NLP.expand_contractions(query)
        nlp = get_spacy_pipeline()
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
    def lemmatize_text(text: str) -> list[str]:
        """Lemmatizes the input text using spaCy."""
        if not text:
            return []

        text = NLP.expand_contractions(text)
        nlp_pipeline = get_spacy_pipeline()
        doc = nlp_pipeline(text)

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
    expanded_query = nlp.expand_query(sample_text)
    print("Lemmatized Tokens:", processed_tokens)
    print("Expanded Query:", expanded_query)
    

