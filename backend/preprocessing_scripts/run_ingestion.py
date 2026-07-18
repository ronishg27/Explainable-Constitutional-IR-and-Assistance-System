"""Run the full offline ingestion pipeline in one command."""

import logging

from preprocessing_scripts.build_index import main as build_index
from preprocessing_scripts.flatten_constitution import main as flatten_constitution
logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("[1/2] Flattening constitution data...")
    flatten_constitution()

    logger.info("[2/2] Building inverted index...")
    build_index()

    logger.info("Ingestion pipeline completed successfully.")


if __name__ == "__main__":
    main()
