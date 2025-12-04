import json
import logging
import sys

from flask import has_request_context, request


class RequestFormatter(logging.Formatter):
    """
    Custom formatter that injects Request ID and User info into logs.
    """

    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    Formatter to output logs as JSON objects (Best for Production/Datadog/ELK).
    """

    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "timestamp": self.formatTime(record, self.datefmt),
            "module": record.module,
        }
        # Add request context if available
        if hasattr(record, "url"):
            log_record["url"] = record.url
            log_record["ip"] = record.remote_addr

        # Handle exceptions
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def configure_logging(app):
    # Remove default handlers
    del app.logger.handlers[:]

    # Send logs to "Standard Output" (so Docker can read them)
    handler = logging.StreamHandler(sys.stdout)

    if app.debug:
        # DEVELOPMENT: Human-readable text
        handler.setFormatter(
            RequestFormatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        )
        app.logger.setLevel(logging.DEBUG)
    else:
        # PRODUCTION: Machine-readable JSON
        handler.setFormatter(JSONFormatter())
        app.logger.setLevel(logging.INFO)

    app.logger.addHandler(handler)

    # Also capture Gunicorn errors if running in prod
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.handlers:
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
