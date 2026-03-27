import time

from flask import Blueprint, current_app, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    try:
        start = time.monotonic()
        current_app.db.command("ping")
        latency_ms = round((time.monotonic() - start) * 1000, 2)
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

    return jsonify({"status": "healthy", "db_latency_ms": latency_ms}), 200
