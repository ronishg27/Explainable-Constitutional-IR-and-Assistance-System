import json
from pathlib import Path

from src.workflows.ingestion_workflow import IngestionWorkflow


def build_inverted_index(documents):
    """Build inverted index from documents using normalized word tokens only."""
    return IngestionWorkflow.build_inverted_index(documents)

def build_positional_inverted_index(documents):
    """Build positional inverted index from documents using normalized word tokens only."""
    return IngestionWorkflow.build_positional_inverted_index(documents)


def main():
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data" / "output" / "flattened_nepal_constitution.json"
    output_path = root / "data" / "output" / "inverted_index.json"
    pos_output_path = root / "data" / "output" / "positional_inverted_index.json"
    ingestion = IngestionWorkflow(str(input_path))

    print(f"Loading documents from {input_path.name}...")
    documents = ingestion.load_documents()

    print(f"Building inverted index from {len(documents)} documents...")
    index = ingestion.build_inverted_index(documents)
    
    print(f"Building positional inverted index from {len(documents)} documents...")
    pos_index = ingestion.build_positional_inverted_index(documents)

    print(f"Saving inverted index to {output_path.name}...")
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        
    print(f"Saving positional inverted index to {pos_output_path.name}...")
    with pos_output_path.open("w", encoding="utf-8") as f:
        json.dump(pos_index, f, indent=2, ensure_ascii=False)

    print(f"\nInverted index statistics:")
    print(f"  Total documents: {len(documents)}")
    print(f"  Unique terms: {len(index)}")
    print(f"  Output file: {output_path}")
    print(f"  Positional inverted index file: {pos_output_path}")

if __name__ == "__main__":
    main()
