import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[0]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.constants.stopwords import STOPWORDS


def tokenize(text):
    if not text:
        return []

    normalized_text = text.lower()
    normalized_text = re.sub(r'[^\w\s]', ' ', normalized_text)
    tokens = normalized_text.split()
    return [token for token in tokens if token not in STOPWORDS]
