# -*- coding: utf-8 -*-
"""HTTP route modules — registers all Flask Blueprints."""

from app.routes.auth import auth_bp
from app.routes.checker import checker_bp
from app.routes.dashboard import dashboard_bp
from app.routes.pages import pages_bp
from app.routes.profile import profile_bp
from app.routes.reports import reports_bp


def register_blueprints(app):
    """Register all route blueprints with the Flask application."""
    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(checker_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(reports_bp)
