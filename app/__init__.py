from flask import Flask

from app.models.user_store import init_db
from app.routes.main import register_routes
from config import Config


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    app.config.from_object(Config)

    init_db(app.config["DATABASE_PATH"])
    register_routes(app)
    return app


# Expose a global Flask app for Gunicorn target: `app:app`.
app = create_app()
