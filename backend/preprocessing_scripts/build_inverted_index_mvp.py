import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from text_processing import tokenize


def build_inverted_index(documents):
    """Build inverted index from documents using body_tokens."""
    index = {}
    
    for doc in documents:
        doc_id = doc["doc_id"]
        tokens = doc.get("body_tokens", tokenize(doc["text"]))
        
        for token in tokens:
            if token not in index:
                index[token] = {}
            index[token][doc_id] = index[token].get(doc_id, 0) + 1
    
    return index


def main():
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data" / "flattened_nepal_constitution.json"
    output_path = root / "data" / "inverted_index_mvp.json"

    print(f"Loading documents from {input_path.name}...")
    with input_path.open("r", encoding="utf-8") as f:
        documents = json.load(f)

    print(f"Building inverted index from {len(documents)} documents...")
    index = build_inverted_index(documents)

    print(f"Saving inverted index to {output_path.name}...")
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\nInverted index statistics:")
    print(f"  Total documents: {len(documents)}")
    print(f"  Unique terms: {len(index)}")
    print(f"  Output file: {output_path}")


if __name__ == "__main__":
    main()
