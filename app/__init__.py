from flask import Flask
from pymongo import MongoClient

from .config import Config, config_map
from .errors import register_error_handlers
from .health import health_bp
from .logging_config import setup_logging
from .metrics import metrics_bp, register_metrics
from .middleware import register_middleware
from .routes import tracks_bp


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, Config))

    # Store the client on the app so extensions and tests can reach it via
    # current_app without relying on a global variable.
    client = MongoClient(app.config["MONGO_URI"])
    app.mongo = client

    # The database name is the last segment of the URI; parse it here so
    # routes can access app.db without repeating the URI parsing logic.
    db_name = app.config["MONGO_URI"].rstrip("/").split("/")[-1] or "musiccatalog"
    app.db = client[db_name]

    setup_logging(app)
    register_middleware(app)
    register_metrics(app)
    app.register_blueprint(health_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(tracks_bp)
    register_error_handlers(app)

    return app
