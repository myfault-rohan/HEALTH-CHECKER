# -*- coding: utf-8 -*-
"""Static / public page routes: landing, about, contact."""

import logging

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models.user_store import normalize_email
from app.routes.helpers import EMAIL_REGEX, clean_text

logger = logging.getLogger(__name__)

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("dashboard.dashboard"))
    return render_template("index.html", show_steps=False, show_sidebar=False)


@pages_bp.route("/about")
def about():
    return render_template("about.html", show_steps=False, show_sidebar=False)


@pages_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = clean_text(request.form.get("name"), max_length=80)
        email = normalize_email(request.form.get("email"))
        message = clean_text(request.form.get("message"), max_length=600)

        if not name or not email or not message:
            flash("Please complete all contact fields.", "danger")
        elif not EMAIL_REGEX.match(email):
            flash("Please provide a valid contact email.", "danger")
        else:
            flash("Your message has been received by support.", "success")
            return redirect(url_for("pages.contact"))

    return render_template("contact.html", show_steps=False, show_sidebar=False)
