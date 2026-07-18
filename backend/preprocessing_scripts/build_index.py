"""Build and save all index files using the refactored IngestionWorkflow."""

import logging
from pathlib import Path
from src.workflows.ingestion_workflow import IngestionWorkflow

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data" / "output" / "flattened_nepal_constitution.json"
    output_dir = root / "data" / "output"

    logger.info("Loading documents from %s...", input_path.name)
    workflow = IngestionWorkflow(str(input_path))

    logger.info("Building indexes (tf, positional, doc stats)...")
    workflow.save_indexes(output_dir=str(output_dir))

    logger.info("Index files saved to %s", output_dir)
    logger.info("Done.")


if __name__ == "__main__":
    main()