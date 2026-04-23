import re
import sys
from threading import Lock
from pathlib import Path
import stanza

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from constants.stopwords import STOPWORDS

_stanza_pipeline = None
_stanza_lock = Lock()


def _get_stanza_pipeline():
    global _stanza_pipeline

    if _stanza_pipeline is None:
        with _stanza_lock:
            if _stanza_pipeline is None:
                _stanza_pipeline = stanza.Pipeline(
                    lang='en',
                    processors='tokenize,mwt,lemma',
                    download_method=None,
                )

    return _stanza_pipeline

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
    def stanza_lemmatize(text):
        """Lemmatizes the input text using Stanza."""
        
        doc = _get_stanza_pipeline()(text)
        lemmatized_tokens = [word.lemma for sentence in doc.sentences for word in sentence.words]
        filtered_tokens = [token for token in lemmatized_tokens if token not in STOPWORDS]
        normalized_tokens = NLP.normalize(' '.join(filtered_tokens)).split()
        return normalized_tokens



if __name__ == "__main__":
    nlp = NLP()
    sample_text = "The quick brown foxes were jumping over the lazy dogs. They've been doing this for years! Isn't it amazing?  "
    # processed_tokens = nlp.preprocess(sample_text)
    processed_tokens = nlp.stanza_lemmatize(sample_text)
    print(processed_tokens)
    

