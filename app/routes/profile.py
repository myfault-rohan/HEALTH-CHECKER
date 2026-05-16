# -*- coding: utf-8 -*-
"""Profile routes: profile view, CSV export, history management."""

import csv
import io
import logging

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)

from app.models.user_store import (
    clear_history_entries,
    delete_history_entry,
    get_history_entries,
    normalize_email,
)

from app.routes.helpers import (
    build_history_stats,
    login_required,
)

logger = logging.getLogger(__name__)

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def profile():
    email = normalize_email(session.get("email"))
    history = get_history_entries(email)
    stats = build_history_stats(history)
    return render_template(
        "profile.html",
        history=history,
        stats=stats,
        email=email,
        show_steps=False,
        show_sidebar=False,
    )


@profile_bp.route("/profile/export-csv")
@login_required
def export_profile_csv():
    email = normalize_email(session.get("email"))
    history = get_history_entries(email)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "symptoms", "top_condition", "urgency"])
    for entry in history:
        writer.writerow(
            [
                entry.get("date", ""),
                ", ".join(entry.get("symptoms", [])),
                entry.get("top_condition", ""),
                entry.get("top_urgency", ""),
            ]
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="health-history.csv"'
        },
    )


@profile_bp.route("/profile/history/delete/<int:entry_id>", methods=["POST"])
@login_required
def delete_profile_history_entry(entry_id):
    email = normalize_email(session.get("email"))
    if not email:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    deleted = delete_history_entry(email, entry_id)
    if deleted:
        flash("History entry deleted.", "success")
    else:
        flash("History entry not found.", "warning")
    return redirect(url_for("profile.profile"))


@profile_bp.route("/profile/history/clear", methods=["POST"])
@login_required
def clear_profile_history():
    email = normalize_email(session.get("email"))
    if not email:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    deleted_count = clear_history_entries(email)
    if deleted_count > 0:
        flash(f"Deleted {deleted_count} history record(s).", "success")
    else:
        flash("No history records to delete.", "info")
    return redirect(url_for("profile.profile"))
