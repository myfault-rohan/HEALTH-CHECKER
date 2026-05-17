"""Dashboard routes: patient dashboard, doctor dashboard, stats API."""

import logging

from flask import (
    Blueprint,
    jsonify,
    render_template,
    session,
)

from app.models.user_store import (
    get_history_entries,
    normalize_email,
)
from app.routes.helpers import (
    build_history_stats,
    checker_sidebar_context,
    login_required,
)

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    email = normalize_email(session.get("email"))
    history = get_history_entries(email) if email else []
    stats = build_history_stats(history)
    sidebar = checker_sidebar_context()
    return render_template(
        "dashboard.html",
        show_steps=False,
        show_sidebar=False,
        email=email,
        age=sidebar["age"],
        gender=sidebar["gender"],
        history=history[:5],
        stats=stats,
    )


@dashboard_bp.route("/doctor/dashboard")
@login_required
def doctor_dashboard():
    from app.models.user_store import get_clinic_check_results
    results = get_clinic_check_results(limit=50)
    total_checks = len(results)
    high_urgency = sum(
        1 for r in results
        if r.get("condition_details") and r["condition_details"][0].get("urgency") == "high"
    )
    return render_template(
        "doctor_dashboard.html",
        results=results,
        total_checks=total_checks,
        high_urgency=high_urgency,
        show_steps=False,
        show_sidebar=False
    )


@dashboard_bp.route("/api/history-stats")
@login_required
def history_stats():
    email = normalize_email(session.get("email"))
    history = get_history_entries(email) if email else []
    return jsonify(build_history_stats(history))
