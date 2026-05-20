import logging
import os

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from prometheus_flask_exporter import PrometheusMetrics

limiter = Limiter(key_func=get_remote_address, default_limits=[], storage_uri="memory://")


def _configure_logging():
    """Set up structured logging for the entire application."""
    is_production = os.getenv("FLASK_ENV", "").strip().lower() == "production"
    level = logging.INFO if is_production else logging.DEBUG
    fmt = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        if is_production
        else "%(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )
    logging.basicConfig(level=level, format=fmt, force=True)
    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def create_app():
    _configure_logging()

    from config import Config

    from app.models.user_store import init_db
    from app.routes import register_blueprints

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    app.config.from_object(Config)

    init_db(app.config["DATABASE_PATH"])
    limiter.init_app(app)
    # Prometheus metrics — exposes /metrics endpoint
    metrics = PrometheusMetrics(app, default_labels={"app": "health-checker-pro"})
    metrics.info("app_info", "Health Checker Pro", version="2.0.0")
    register_blueprints(app)

    logger = logging.getLogger(__name__)
    logger.info("Health Checker Pro started successfully")
    return app
