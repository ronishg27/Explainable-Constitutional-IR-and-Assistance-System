import logging
import logging.handlers
import os
import uuid

from flask import Flask, g
from flask_cors import CORS
from dotenv import load_dotenv

from src.core.app_bootstrap import connect_database, rebuild_document_artifacts, preload_spacy

load_dotenv(dotenv_path=".env", override=True)


class CorrelationFilter(logging.Filter):
    """Inject request correlation ID into log records when available."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from flask import has_request_context, request
            if has_request_context():
                record.correlation_id = getattr(g, "correlation_id", "-")
            else:
                record.correlation_id = "-"
        except Exception:
            record.correlation_id = "-"
        return True


def setup_logging() -> None:
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  [%(correlation_id)s]  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "backend.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addFilter(CorrelationFilter())


def register_request_hooks(app: Flask) -> None:
    @app.before_request
    def assign_correlation_id():
        g.correlation_id = uuid.uuid4().hex[:12]


logger = logging.getLogger(__name__)


def create_app():
    from routes.api_routes import api_bp
    from routes.auth_routes import auth_bp

    app = Flask(__name__)
    CORS(app, supports_credentials=True)

    register_request_hooks(app)
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
    setup_logging()

    args = parse_args()

    if args.rebuild_data:
        rebuild_document_artifacts(logger)

    preload_spacy()
    app = create_app()

    logger.info("Starting the Flask API server...")
    app.run(debug=True)


if __name__ == "__main__":
    main()
