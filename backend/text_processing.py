import re


from .src.constants import STOPWORDS


def tokenize(text):
    if not text:
        return []

    normalized_text = text.lower()
    normalized_text = re.sub(r'[^\w\s]', ' ', normalized_text)
    tokens = normalized_text.split()
    return [token for token in tokens if token not in STOPWORDS]
