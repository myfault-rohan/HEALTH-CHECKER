from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[], storage_uri="memory://")


def create_app():
    from app.models.user_store import init_db
    from app.routes.main import register_routes
    from config import Config

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    app.config.from_object(Config)

    init_db(app.config["DATABASE_PATH"])
    limiter.init_app(app)
    register_routes(app)
    return app
