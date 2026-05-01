import os
from logging import Logger

from config.db_connect import Database


def rebuild_document_artifacts(logger: Logger) -> None:
    from preprocessing_scripts.build_index import main as build_index
    from preprocessing_scripts.flatten_constitution import main as flatten_constitution
    from preprocessing_scripts.generate_safe_lemma_dict import main as generate_lemma_dict

    logger.info("Rebuilding document artifacts from data/nepal_constitution.json")
    flatten_constitution()
    build_index()
    generate_lemma_dict()


def preload_spacy() -> None:
    from src.core.text_processor import get_spacy_pipeline

    get_spacy_pipeline()


def connect_database() -> None:
    db = Database()
    db_name = os.getenv("MONGO_DB_NAME", "ECIRAS")
    host = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db.connect(db_name=db_name, host=host)
