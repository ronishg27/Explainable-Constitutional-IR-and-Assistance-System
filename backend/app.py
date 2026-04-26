import argparse
import logging
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from config.db_connect import Database
from preprocessing_scripts.build_inverted_index_mvp import main as build_inverted_index
from preprocessing_scripts.flatten_constitution import main as flatten_constitution
from preprocessing_scripts.generate_safe_lemma_dict import main as generate_lemma_dict

# load env vars
load_dotenv(dotenv_path=".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# load spacy pipeline to warm up the model and avoid first request latency
from core.preprocessing import get_spacy_pipeline
get_spacy_pipeline()

def rebuild_document_artifacts():
    logging.info("Rebuilding document artifacts from data/nepal_constitution_mvp.json")
    flatten_constitution()
    build_inverted_index()
    generate_lemma_dict()

def create_app():
    from routes.api_routes import api_bp
    from routes.auth_routes import auth_bp

    app = Flask(__name__)
    CORS(app)

    db = Database()
    DB_NAME = os.getenv("MONGO_DB_NAME", "ECIRAS")
    HOST = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db.connect(db_name=DB_NAME, host=HOST)

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    return app


def parse_args():
    parser = argparse.ArgumentParser(description="Constitution assistant API server")
    parser.add_argument(
        "--rebuild-data",
        action="store_true",
        help="Rebuild flattened documents, inverted index, and lemma dictionary before starting the server.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.rebuild_data:
        rebuild_document_artifacts()

    app = create_app()

    logger.info("Starting the Flask API server...")
    # NOTE: debug=True should only for development
    app.run(debug=True)


if __name__ == "__main__":
    main()
    