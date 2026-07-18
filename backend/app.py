import logging
import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from config.db_connect import Database
from config.log_config import setup_logging
from services.qa_service import init_workflow

from routes.api_routes import api_bp
from routes.auth_routes import auth_bp
from src.core.text_processor import get_spacy_pipeline

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    Database().connect(
        db_name=os.getenv("MONGO_DB_NAME", "ECIRAS"),
        host=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    )
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    return app


def main():
    load_dotenv(dotenv_path=".env", override=True)
    setup_logging()
    init_workflow()
    get_spacy_pipeline()

    app = create_app()

    logger.info("Starting the Flask API server...")
    try:
        app.run(debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Closing the server")
    except Exception as e:
        logger.error(f"An error occurred while running the server: {e}")


if __name__ == "__main__":
    main()
