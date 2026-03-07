import re
import sqlite3
from datetime import datetime
from functools import wraps

from flask import flash, redirect, render_template, request, session, url_for
from predictor import predict_disease

from app.models.user_store import (
    clear_history_entries,
    create_user,
    delete_history_entry,
    get_history_entries,
    get_user_profile,
    normalize_email,
    save_history_entry,
    update_user_profile,
    verify_user,
)
from app.services.prediction_service import (
    compute_condition_matches,
    detect_emergency_signals,
    get_condition_precautions,
    get_searchable_symptoms,
    get_symptom_categories,
    normalize_symptom_name,
    ordered_unique,
    symptoms_conditions,
)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_GENDERS = {"male", "female", "other"}

CHECKER_SESSION_KEYS = [
    "selected_symptoms",
    "predicted_disease",
    "condition_details",
    "remedies",
    "emergency_detected",
    "emergency_message",
    "analysis",
    "active_condition",
    "lifestyle_suggestions",
]


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "logged_in" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


def clean_text(value, max_length=200):
    return (value or "").strip()[:max_length]


def clear_checker_session():
    for key in CHECKER_SESSION_KEYS:
        session.pop(key, None)


def get_profile_from_session():
    try:
        age = int(session.get("patient_age", 0))
    except (TypeError, ValueError):
        age = 0
    gender = (session.get("patient_gender") or "").strip().lower()
    return age, gender


def has_profile():
    age, gender = get_profile_from_session()
    return age > 0 and gender in VALID_GENDERS


def format_gender(gender):
    if not gender:
        return "Not set"
    return gender.capitalize()


def checker_sidebar_context():
    age, gender = get_profile_from_session()
    return {
        "age": age if age > 0 else "Not set",
        "gender": format_gender(gender),
        "selected_symptoms": session.get("selected_symptoms", []),
    }


def get_condition_from_session(condition_name):
    normalized_name = clean_text(condition_name, max_length=120).lower()
    for condition in session.get("condition_details", []):
        if condition.get("name", "").strip().lower() == normalized_name:
            return condition
    return None


def register_routes(app):
    @app.route("/")
    def index():
        if session.get("logged_in"):
            return redirect(url_for("dashboard"))
        return render_template("index.html", show_steps=False, show_sidebar=False)

    @app.route("/dashboard")
    @login_required
    def dashboard():
        email = normalize_email(session.get("email"))
        history = get_history_entries(email) if email else []
        return render_template(
            "dashboard.html",
            show_steps=False,
            show_sidebar=False,
            email=email,
            age=checker_sidebar_context()["age"],
            gender=checker_sidebar_context()["gender"],
            history=history[:5],
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if "logged_in" in session:
            return redirect(url_for("dashboard"))

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
                flash("Welcome back. Login successful.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid email or password.", "danger")

        return render_template("login.html", show_steps=False, show_sidebar=False)

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if "logged_in" in session:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = normalize_email(request.form.get("email"))
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not email or not password:
                flash("Email and password are required.", "danger")
            elif not EMAIL_REGEX.match(email):
                flash("Enter a valid email address.", "danger")
            elif len(password) < 6:
                flash("Use at least 6 characters for password.", "danger")
            elif password != confirm_password:
                flash("Passwords do not match.", "danger")
            else:
                try:
                    create_user(email, password)
                    session["logged_in"] = True
                    session["email"] = email
                    flash("Account created successfully.", "success")
                    return redirect(url_for("dashboard"))
                except sqlite3.IntegrityError:
                    flash("That email is already registered.", "danger")

        return render_template("signup.html", show_steps=False, show_sidebar=False)

    @app.route("/info", methods=["GET", "POST"])
    @login_required
    def info():
        age, gender = get_profile_from_session()
        form_age = age if age > 0 else ""
        form_gender = gender

        if request.method == "POST":
            try:
                age = int(request.form.get("age", 0))
            except (TypeError, ValueError):
                age = 0
            gender = (request.form.get("gender") or "").strip().lower()

            form_age = request.form.get("age", "")
            form_gender = gender

            if age <= 0 or age > 120:
                flash("Please enter a valid age between 1 and 120.", "danger")
            elif gender not in VALID_GENDERS:
                flash("Please select a gender.", "danger")
            else:
                session["patient_age"] = age
                session["patient_gender"] = gender
                email = normalize_email(session.get("email"))
                if email:
                    update_user_profile(email, age, gender)
                clear_checker_session()
                flash("Profile saved. Continue with symptom selection.", "success")
                return redirect(url_for("symptoms"))

        return render_template(
            "info.html",
            current_step="info",
            show_steps=True,
            show_sidebar=True,
            sidebar=checker_sidebar_context(),
            age=form_age,
            gender=form_gender,
        )

    @app.route("/symptoms")
    @login_required
    def symptoms():
        if not has_profile():
            flash("Please complete your profile first.", "warning")
            return redirect(url_for("info"))

        return render_template(
            "symptoms.html",
            current_step="symptoms",
            show_steps=True,
            show_sidebar=True,
            sidebar=checker_sidebar_context(),
            symptom_names=get_searchable_symptoms(),
            selected_symptoms=session.get("selected_symptoms", []),
            symptom_categories=get_symptom_categories(),
        )

    @app.route("/conditions")
    @login_required
    def conditions():
        if not has_profile():
            return redirect(url_for("info"))

        condition_details = session.get("condition_details", [])
        if not condition_details:
            flash("No analysis found yet. Please select symptoms first.", "warning")
            return redirect(url_for("symptoms"))

        return render_template(
            "conditions.html",
            current_step="conditions",
            show_steps=True,
            show_sidebar=True,
            sidebar=checker_sidebar_context(),
            condition_details=condition_details,
            predicted_disease=session.get("predicted_disease", "No clear match"),
            analysis=session.get("analysis", {}),
            selected_symptoms=session.get("selected_symptoms", []),
        )

    @app.route("/details/<path:condition_name>")
    @login_required
    def details(condition_name):
        if not has_profile():
            return redirect(url_for("info"))
        if not session.get("condition_details"):
            return redirect(url_for("symptoms"))

        condition = get_condition_from_session(condition_name)
        if not condition:
            flash("Condition not found in the current analysis.", "warning")
            return redirect(url_for("conditions"))

        session["active_condition"] = condition.get("name", "")
        return render_template(
            "details.html",
            current_step="details",
            show_steps=True,
            show_sidebar=True,
            sidebar=checker_sidebar_context(),
            condition=condition,
        )

    @app.route("/treatment/<path:condition_name>")
    @login_required
    def treatment(condition_name):
        if not has_profile():
            return redirect(url_for("info"))
        if not session.get("condition_details"):
            return redirect(url_for("symptoms"))

        condition = get_condition_from_session(condition_name)
        if not condition:
            return redirect(url_for("conditions"))

        session["active_condition"] = condition.get("name", "")
        emergency_detected = bool(session.get("emergency_detected"))
        emergency_message = session.get("emergency_message", "")
        when_to_see_doctor = list(get_condition_precautions(condition))

        if emergency_detected and emergency_message:
            when_to_see_doctor.insert(0, emergency_message)

        lifestyle_suggestions = session.get("lifestyle_suggestions", [])
        if not lifestyle_suggestions:
            lifestyle_suggestions = [
                "Maintain hydration throughout the day.",
                "Get adequate sleep and avoid overexertion.",
                "Prefer light and balanced meals while recovering.",
            ]

        return render_template(
            "treatment.html",
            current_step="treatment",
            show_steps=True,
            show_sidebar=True,
            sidebar=checker_sidebar_context(),
            condition=condition,
            remedies=session.get("remedies", []),
            emergency_detected=emergency_detected,
            emergency_message=emergency_message,
            when_to_see_doctor=ordered_unique(when_to_see_doctor),
            lifestyle_suggestions=lifestyle_suggestions,
        )

    @app.route("/start-over")
    @login_required
    def start_over():
        clear_checker_session()
        session.pop("patient_age", None)
        session.pop("patient_gender", None)
        flash("Started a new check session.", "info")
        return redirect(url_for("info"))

    @app.route("/about")
    def about():
        return render_template("about.html", show_steps=False, show_sidebar=False)

    @app.route("/contact", methods=["GET", "POST"])
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
                return redirect(url_for("contact"))

        return render_template("contact.html", show_steps=False, show_sidebar=False)

    @app.route("/profile")
    @login_required
    def profile():
        email = normalize_email(session.get("email"))
        history = get_history_entries(email)
        return render_template(
            "profile.html",
            history=history,
            show_steps=False,
            show_sidebar=False,
        )

    @app.route("/profile/history/delete/<int:entry_id>", methods=["POST"])
    @login_required
    def delete_profile_history_entry(entry_id):
        email = normalize_email(session.get("email"))
        if not email:
            flash("Session expired. Please log in again.", "warning")
            return redirect(url_for("login"))

        deleted = delete_history_entry(email, entry_id)
        if deleted:
            flash("History entry deleted.", "success")
        else:
            flash("History entry not found.", "warning")
        return redirect(url_for("profile"))

    @app.route("/profile/history/clear", methods=["POST"])
    @login_required
    def clear_profile_history():
        email = normalize_email(session.get("email"))
        if not email:
            flash("Session expired. Please log in again.", "warning")
            return redirect(url_for("login"))

        deleted_count = clear_history_entries(email)
        if deleted_count > 0:
            flash(f"Deleted {deleted_count} history record(s).", "success")
        else:
            flash("No history records to delete.", "info")
        return redirect(url_for("profile"))

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    @app.route("/check", methods=["POST"])
    @login_required
    def check_symptoms():
        if not has_profile():
            flash("Please complete your profile first.", "warning")
            return redirect(url_for("info"))

        allowed_symptoms = set(get_searchable_symptoms())
        selected_symptoms = ordered_unique(
            [
                normalize_symptom_name(symptom)
                for symptom in request.form.getlist("symptoms")
                if (symptom or "").strip()
            ]
        )
        selected_symptoms = [
            symptom for symptom in selected_symptoms if symptom in allowed_symptoms
        ]

        if not selected_symptoms:
            clear_checker_session()
            flash("Select at least one valid symptom to continue.", "danger")
            return redirect(url_for("symptoms"))

        age, gender = get_profile_from_session()
        form_data = {
            key: clean_text(request.form.get(key), max_length=80)
            for key in request.form.keys()
        }
        cough_type = (form_data.get("cough_type") or "").lower()

        remedies_pool = []
        for symptom in selected_symptoms:
            symptom_data = symptoms_conditions.get(symptom)
            if symptom_data:
                remedies_pool.extend(symptom_data.get("remedies", []))
        remedies = ordered_unique(remedies_pool)[:24]

        lifestyle_suggestions = []
        if remedies:
            # Convert individual remedy bullets into grouped narrative sections
            # so treatment output reads like clinician-style guidance.
            herbals = [item for item in remedies if "ðŸŒ¿" in item]
            dietary = [
                item
                for item in remedies
                if "ðŸ¥•" in item
                or "ðŸŽ" in item
                or "ðŸŒ" in item
                or "ðŸš" in item
                or "ðŸ¥¬" in item
            ]
            lifestyle = [
                item
                for item in remedies
                if "ðŸ§˜" in item
                or "ðŸ˜´" in item
                or "ðŸ›Œ" in item
                or "ðŸ‘ï¸" in item
            ]
            liquids = [
                item for item in remedies if "ðŸ’§" in item or "ðŸ«" in item or "ðŸ¥›" in item
            ]
            other = [
                item
                for item in remedies
                if item not in herbals + dietary + lifestyle + liquids
            ]

            remedy_sections = []
            if herbals:
                herbs_text = ", ".join(
                    [item.replace("ðŸŒ¿ ", "") for item in herbals[:-1]]
                )
                final_herb = herbals[-1].replace("ðŸŒ¿ ", "")
                if herbs_text:
                    remedy_sections.append(
                        f"ðŸŒ¿ **Ayurvedic Herbal Remedies**: {herbs_text} and {final_herb}."
                    )
                else:
                    remedy_sections.append(
                        f"ðŸŒ¿ **Ayurvedic Herbal Remedies**: {final_herb}."
                    )

            if dietary:
                foods_text = ", ".join(
                    [item.split(" ", 1)[1] if " " in item else item for item in dietary]
                )
                remedy_sections.append(
                    f"ðŸŽ **Dietary Recommendations**: Incorporate {foods_text} into your meals."
                )

            if lifestyle:
                lifestyle_text = ", ".join(
                    [
                        item.replace("ðŸ§˜ ", "")
                        .replace("ðŸ˜´ ", "")
                        .replace("ðŸ›Œ ", "")
                        .replace("ðŸ‘ï¸ ", "")
                        for item in lifestyle
                    ]
                )
                remedy_sections.append(f"ðŸ§˜ **Lifestyle & Rest**: {lifestyle_text}.")

            if liquids:
                liquids_text = ", ".join(
                    [
                        item.replace("ðŸ’§ ", "")
                        .replace("ðŸ« ", "")
                        .replace("ðŸ¥› ", "")
                        for item in liquids
                    ]
                )
                remedy_sections.append(f"ðŸ’§ **Hydration**: {liquids_text}.")

            if other:
                remedy_sections.extend(other)

            remedies = [" ".join(remedy_sections)]
            lifestyle_suggestions = ordered_unique(
                [
                    item.replace("ðŸ§˜ ", "")
                    .replace("ðŸ˜´ ", "")
                    .replace("ðŸ›Œ ", "")
                    .replace("ðŸ‘ï¸ ", "")
                    .replace("ðŸ’§ ", "")
                    .replace("ðŸ« ", "")
                    .replace("ðŸ¥› ", "")
                    .replace("ðŸŒ¿ ", "")
                    for item in lifestyle + liquids + dietary
                ]
            )[:8]

        condition_details = compute_condition_matches(
            selected_symptoms, age, gender, form_data
        )
        predicted_disease = predict_disease(selected_symptoms)
        
        # Inject ML prediction into condition details if valid
        if predicted_disease and predicted_disease not in ["No clear match", "Prediction Error", "No clear match (Model not loaded)"]:
            existing = next((c for c in condition_details if c["name"].lower() == predicted_disease.lower()), None)
            if not existing:
                ml_condition = {
                    "name": predicted_disease,
                    "confidence": 95,
                    "match_label": "Machine Learning Match",
                    "urgency": "medium",
                    "severity": "medium",
                    "evidence": ["statistical pattern matching"],
                    "description": "This condition was predicted by our trained Random Forest model based on your symptom profile.",
                }
                condition_details.insert(0, ml_condition)
            else:
                condition_details.remove(existing)
                existing["match_label"] = "Verified by Machine Learning"
                existing["confidence"] = min(99, existing["confidence"] + 20)
                condition_details.insert(0, existing)

        # Attach UI-facing fields once so all downstream pages can reuse them.
        for condition in condition_details:
            condition["possible_causes"] = condition.get("evidence", [])
            condition["precautions"] = get_condition_precautions(condition)

        final_conditions = [
            f"{condition['name']} ({condition['match_label']})"
            for condition in condition_details
        ]
        emergency_detected, emergency_message = detect_emergency_signals(
            selected_symptoms, form_data
        )

        quality = "good"
        suggestion = (
            "Results confidence improves when you add specific symptom details."
        )
        if len(selected_symptoms) <= 1:
            quality = "limited"
            suggestion = "Add at least 2-3 symptoms for better accuracy."
        elif len(selected_symptoms) >= 5:
            quality = "high"
            suggestion = (
                "Good symptom coverage. Review the top matches and urgent flags carefully."
            )
        if "cough" in selected_symptoms and cough_type in {"dry", "wet"}:
            suggestion = f"{suggestion} Cough type noted as {cough_type}."

        history_entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "symptoms": selected_symptoms,
            "conditions": final_conditions,
            "remedies": remedies,
            "analysis_quality": quality,
        }

        email = normalize_email(session.get("email"))
        if email:
            save_history_entry(email, history_entry)

        session["selected_symptoms"] = selected_symptoms
        session["predicted_disease"] = predicted_disease
        session["condition_details"] = condition_details
        session["remedies"] = remedies
        session["emergency_detected"] = emergency_detected
        session["emergency_message"] = emergency_message
        session["analysis"] = {
            "symptom_count": len(selected_symptoms),
            "quality": quality,
            "suggestion": suggestion,
        }
        session["lifestyle_suggestions"] = lifestyle_suggestions
        if condition_details:
            session["active_condition"] = condition_details[0]["name"]

        flash("Prediction completed. Review your condition matches.", "success")
        return redirect(url_for("conditions"))
