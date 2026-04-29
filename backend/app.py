import logging

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from src.core.app_bootstrap import connect_database, rebuild_document_artifacts, warm_up_spacy

load_dotenv(dotenv_path=".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    from routes.api_routes import api_bp
    from routes.auth_routes import auth_bp

    app = Flask(__name__)
    CORS(app)

    connect_database()

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    return app


def parse_args():
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Constitution assistant API server")
    parser.add_argument(
        "--rebuild-data",
        action="store_true",
        help="Rebuild flattened documents, inverted index, and lemma dictionary before starting the server.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.rebuild_data:
        rebuild_document_artifacts(logger)

    warm_up_spacy()
    app = create_app()

    logger.info("Starting the Flask API server...")
    app.run(debug=True)


if __name__ == "__main__":
    main()
    