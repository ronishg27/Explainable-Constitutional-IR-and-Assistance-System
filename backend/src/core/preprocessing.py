

import json
import re
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from constants.stopwords import STOPWORDS


class NLP:
    def __init__(self):
        root_dir = Path(__file__).resolve().parents[2]
        lemma_path = root_dir / "data" / "lemma_dict_v3.json"
        with lemma_path.open("r", encoding="utf-8") as f:
            self.lemma_dict = json.load(f)


    def preprocess(self, text):
        """Preprocesses the input text by normalizing, tokenizing, and removing stopwords."""
        normalized_text = self.normalize(text)
        tokens = self.tokenize(normalized_text)
        filtered_tokens = self.remove_stopwords(tokens)
        lemmatized_tokens = self.lemmatize(filtered_tokens)
        return lemmatized_tokens

    def normalize(self, text):
        """Normalizes the input text by converting it to lowercase and removing punctuation."""
        if not text:
            return ""

        normalized_text = text.lower()
        normalized_text = re.sub(r'[^\w\s]', ' ', normalized_text)
        return normalized_text


    def tokenize(self, text):
        """Tokenizes the input text into a list of tokens."""
        if not text:
            return []
        
        tokens = text.split()
        return tokens
    
    def remove_stopwords(self, tokens):
        """Removes stopwords from the list of tokens."""
        return [token for token in tokens if token not in STOPWORDS]
    

    def lemmatize(self, tokens):
        """Lemmatizes the input tokens to their base forms."""
        return [self.lemma_dict.get(token, token) for token in tokens]



if __name__ == "__main__":
    nlp = NLP()
    sample_text = "The quick brown foxes were jumping over the lazy dogs. They've been doing this for years! Isn't it amazing?  "
    processed_tokens = nlp.preprocess(sample_text)
    print(processed_tokens)
    

