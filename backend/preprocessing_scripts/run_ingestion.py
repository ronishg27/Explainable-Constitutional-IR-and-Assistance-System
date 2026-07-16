"""Run the full offline ingestion pipeline in one command."""

import logging

from preprocessing_scripts.build_index import main as build_index
from preprocessing_scripts.flatten_constitution import main as flatten_constitution
from preprocessing_scripts.generate_safe_lemma_dict import main as generate_safe_lemma_dict

logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("[1/3] Flattening constitution data...")
    flatten_constitution()

    logger.info("[2/3] Building inverted index...")
    build_index()

    logger.info("[3/3] Generating lemma dictionary...")
    generate_safe_lemma_dict()

    logger.info("Ingestion pipeline completed successfully.")


if __name__ == "__main__":
    main()
