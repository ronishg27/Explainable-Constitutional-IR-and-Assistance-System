"""Build and save all index files using the refactored IngestionWorkflow."""

from pathlib import Path
from src.workflows.ingestion_workflow import IngestionWorkflow


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data" / "output" / "flattened_nepal_constitution.json"
    output_dir = root / "data" / "output"

    print(f"Loading documents from {input_path.name}...")
    workflow = IngestionWorkflow(str(input_path))

    print("Building indexes (tf, positional, doc stats)...")
    workflow.save_indexes(output_dir=str(output_dir))

    print(f"Index files saved to {output_dir}")
    print("Done.")


if __name__ == "__main__":
    main()