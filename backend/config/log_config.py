import logging
import logging.handlers
import os

from flask import has_request_context, request


class ContextFilter(logging.Filter):
    """Inject HTTP method and route into log records when available."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if has_request_context():
                record.method = request.method
                record.route = request.path
            else:
                record.method = "SYSTEM"
                record.route = "-"
        except Exception:
            record.method = "SYSTEM"
            record.route = "-"
        return True


def setup_logging() -> None:
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(method)-6s  %(route)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        defaults={"method": "SYSTEM", "route": "-"},
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

    console_handler.addFilter(ContextFilter())
    file_handler.addFilter(ContextFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
