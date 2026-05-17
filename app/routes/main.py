"""Legacy compatibility shim.

The actual route implementations have been split into separate blueprint
modules under ``app/routes/``.  This file is kept only to preserve the
``register_routes()`` entry-point that the app factory historically called,
and it now simply delegates to the new blueprint registration function.

Blueprint modules:
  - auth.py       – login, signup, logout
  - checker.py    – info, symptoms, check, conditions, details, treatment
  - dashboard.py  – dashboard, doctor dashboard, stats API
  - profile.py    – profile, CSV export, history management
  - reports.py    – PDF download, FHIR export
  - pages.py      – index, about, contact

Shared helpers are in helpers.py.
"""

from app.routes import register_blueprints


def register_routes(app):  # noqa: D103 – kept for backward-compat
    register_blueprints(app)
