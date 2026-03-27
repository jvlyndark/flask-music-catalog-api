import json
import logging
from datetime import datetime, timezone

from flask import Flask, g, has_request_context


class JSONFormatter(logging.Formatter):
    def format(self, record):
        request_id = None
        if has_request_context():
            request_id = getattr(g, "request_id", None)

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": request_id,
        }
        return json.dumps(log_entry)


def setup_logging(app: Flask):
    # Remove Flask's default handlers so log output is purely JSON.
    app.logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
