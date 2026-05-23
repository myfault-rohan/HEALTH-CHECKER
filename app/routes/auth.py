"""Authentication routes: login, signup, logout."""

import logging
import time

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import IntegrityError

from app import limiter
from app.models.user_store import (
    create_user,
    get_user_profile,
    normalize_email,
    verify_user,
)
from app.routes.helpers import EMAIL_REGEX
from app.services.audit_service import AuditAction, log_event

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if "logged_in" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        email = normalize_email(request.form.get("email"))
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
        elif not EMAIL_REGEX.match(email):
            flash("Enter a valid email address.", "danger")
        elif verify_user(email, password):
            session["logged_in"] = True
            session["email"] = email
            profile = get_user_profile(email)
            if profile["age"] > 0:
                session["patient_age"] = profile["age"]
            if profile["gender"]:
                session["patient_gender"] = profile["gender"]
            log_event(email, AuditAction.LOGIN)
            flash("Welcome back. Login successful.", "success")
            return redirect(url_for("dashboard.dashboard"))
        else:
            time.sleep(0.4)
            log_event(email, "LOGIN_FAILED")
            flash("Invalid email or password.", "danger")

    return render_template("login.html", show_steps=False, show_sidebar=False)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if "logged_in" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        email = normalize_email(request.form.get("email"))
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
        elif not EMAIL_REGEX.match(email):
            flash("Enter a valid email address.", "danger")
        elif len(password) < 8:
            flash("Use at least 8 characters for password.", "danger")
        elif password != confirm_password:
            flash("Passwords do not match.", "danger")
        else:
            try:
                create_user(email, password)
                session["logged_in"] = True
                session["email"] = email
                log_event(email, AuditAction.SIGNUP)
                flash("Account created successfully.", "success")
                return redirect(url_for("dashboard.dashboard"))
            except IntegrityError:
                flash("That email is already registered.", "danger")

    return render_template("signup.html", show_steps=False, show_sidebar=False)


@auth_bp.route("/logout")
def logout():
    email = session.get("email", "unknown")
    log_event(email, AuditAction.LOGOUT)
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
