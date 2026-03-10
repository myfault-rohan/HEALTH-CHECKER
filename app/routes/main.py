# -*- coding: utf-8 -*-
import csv
import io
import re
import sqlite3
import time
from collections import Counter
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from markupsafe import Markup, escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app import limiter
from app.models.user_store import (
    clear_history_entries,
    create_user,
    delete_history_entry,
    get_check_result,
    get_history_entries,
    get_latest_check_result,
    get_user_profile,
    normalize_email,
    save_check_result,
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
from predictor import predict_disease

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_GENDERS = {"male", "female", "other"}
CHECKER_SESSION_KEYS = ["last_check_id", "active_condition"]
ICON_PREFIXES = [
    "🌿",
    "💧",
    "😴",
    "🛌",
    "🧘",
    "🍎",
    "🍌",
    "🍚",
    "🥕",
    "🥬",
    "🫐",
    "🥛",
    "👁️",
    "🍵",
    "🚫",
    "🦶",
    "🛁",
    "🥵",
    "🧊",
    "🍋",
    "👕",
]
SYMPTOM_ZONE_MAP = {
    "head": ["headache", "dizziness", "blurred vision", "confusion"],
    "chest": [
        "chest pain",
        "shortness of breath",
        "wheezing",
        "palpitations",
        "cough",
    ],
    "abdomen": [
        "abdominal pain",
        "nausea",
        "vomiting",
        "diarrhea",
        "bloating",
        "heartburn",
    ],
    "arms": ["joint pain", "muscle pain", "swelling", "stiffness"],
    "legs": ["joint pain", "muscle pain", "swelling", "stiffness"],
    "full-body": ["fever", "fatigue", "chills", "weight loss", "insomnia"],
}
BODY_ZONE_TARGETS = {
    "head": "category-neurological",
    "chest": "category-respiratory",
    "abdomen": "category-digestive",
    "arms": "category-musculoskeletal",
    "legs": "category-musculoskeletal",
    "full-body": "category-neurological",
}
CATEGORY_KEYWORDS = {
    "Respiratory": [
        "cold",
        "cough",
        "flu",
        "sinus",
        "bronch",
        "asthma",
        "breath",
        "throat",
        "respir",
        "wheez",
    ],
    "Digestive": [
        "digest",
        "stomach",
        "acid",
        "abdominal",
        "bowel",
        "constipation",
        "diarrhea",
        "vomit",
        "nausea",
        "heartburn",
        "uti",
    ],
    "Neurological": [
        "headache",
        "migraine",
        "vertigo",
        "vision",
        "confusion",
        "anxiety",
        "insomnia",
        "dehydration",
        "fatigue",
        "stress",
    ],
    "Musculoskeletal": [
        "joint",
        "muscle",
        "strain",
        "back",
        "swelling",
        "stiffness",
        "arthritis",
    ],
}
SYMPTOM_RESULTS_TEMPLATE = "_symptom_results.html"


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


def strip_icon_prefix(value):
    text = (value or "").strip()
    for prefix in ICON_PREFIXES:
        if text.startswith(prefix):
            return text.replace(f"{prefix} ", "", 1).replace(prefix, "", 1).strip()
    return text


def parse_datetime_value(value):
    if not value:
        return None

    for parser in (
        lambda raw: datetime.fromisoformat(raw),
        lambda raw: datetime.strptime(raw, "%Y-%m-%d %H:%M"),
    ):
        try:
            return parser(value)
        except (TypeError, ValueError):
            continue
    return None


def format_datetime_label(value):
    parsed = parse_datetime_value(value)
    if not parsed:
        return value or "Unknown"
    return parsed.strftime("%b %d, %Y %I:%M %p")


def format_gender(gender):
    if not gender:
        return "Not set"
    return gender.capitalize()


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


def get_current_check_result(load_latest=False):
    email = normalize_email(session.get("email"))
    if not email:
        return None

    check_id = session.get("last_check_id")
    if check_id:
        result = get_check_result(email, check_id)
        if result:
            return result

    if load_latest:
        result = get_latest_check_result(email)
        if result:
            session["last_check_id"] = result["id"]
        return result
    return None


def checker_sidebar_context():
    age, gender = get_profile_from_session()
    current_result = get_current_check_result()
    return {
        "age": age if age > 0 else "Not set",
        "gender": format_gender(gender),
        "selected_symptoms": (current_result or {}).get("selected_symptoms", []),
    }


def get_condition_from_result(result, condition_name):
    normalized_name = clean_text(condition_name, max_length=120).lower()
    for condition in (result or {}).get("condition_details", []):
        if condition.get("name", "").strip().lower() == normalized_name:
            return condition
    return None


def highlight_match(value, query):
    label = escape(value)
    tokens = [token for token in re.split(r"\s+", query.strip()) if token]
    if not tokens:
        return Markup(label)

    pattern = re.compile(
        "|".join(re.escape(token) for token in sorted(tokens, key=len, reverse=True)),
        re.IGNORECASE,
    )
    highlighted = pattern.sub(
        lambda match: f"<strong>{escape(match.group(0))}</strong>", value
    )
    return Markup(highlighted)


def build_symptom_result_items(query="", zone="", selected_symptoms=None):
    query = clean_text(query, max_length=50).lower()
    zone = clean_text(zone, max_length=20).lower()
    selected_set = {normalize_symptom_name(item) for item in (selected_symptoms or [])}
    searchable = sorted(get_searchable_symptoms())

    if zone and zone in SYMPTOM_ZONE_MAP:
        pool = [item for item in searchable if item in SYMPTOM_ZONE_MAP[zone]]
    else:
        pool = searchable

    query_tokens = [token for token in re.split(r"\s+", query) if token]

    if query:
        scored_pool = []
        for symptom in pool:
            text = symptom.lower()
            words = text.split()
            token_matches = sum(1 for token in query_tokens if token in text)
            prefix_matches = sum(
                1 for token in query_tokens if any(word.startswith(token) for word in words)
            )
            if token_matches == 0:
                continue
            score = token_matches * 10 + prefix_matches * 6
            if text.startswith(query):
                score += 20
            elif query in text:
                score += 8
            if len(query_tokens) > 1 and token_matches == len(query_tokens):
                score += 12
            scored_pool.append((score, len(text), symptom))

        pool = [symptom for _, _, symptom in sorted(scored_pool, key=lambda item: (-item[0], item[1], item[2]))[:12]]
    else:
        pool = pool[:12]

    items = []
    for symptom in pool:
        items.append(
            {
                "id": f"symptom-choice-{symptom.replace(' ', '-')}",
                "value": symptom,
                "checked": symptom in selected_set,
                "highlighted_name": highlight_match(symptom.title(), query),
            }
        )
    return items


def classify_condition(condition):
    search_space = " ".join(
        ordered_unique(
            [
                clean_text(condition.get("name"), max_length=120).lower(),
                *(item.lower() for item in condition.get("evidence", [])),
            ]
        )
    )
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in search_space for keyword in keywords):
            return category
    return "General"


def compute_check_streak(history_entries):
    if not history_entries:
        return 0

    day_values = []
    for entry in history_entries:
        entry_date = (
            parse_datetime_value(entry.get("checked_at"))
            or parse_datetime_value(entry.get("date"))
            or parse_datetime_value(entry.get("created_at"))
        )
        if entry_date:
            day_values.append(entry_date.date())

    unique_days = sorted(set(day_values), reverse=True)
    if not unique_days:
        return 0

    streak = 1
    current_day = unique_days[0]
    for next_day in unique_days[1:]:
        if current_day - next_day == timedelta(days=1):
            streak += 1
            current_day = next_day
            continue
        break
    return streak


def build_history_stats(history_entries):
    symptom_counter = Counter()
    category_counter = Counter()

    for entry in history_entries:
        symptom_counter.update(entry.get("symptoms", []))
        summaries = entry.get("condition_summaries") or []
        if summaries:
            for condition in summaries:
                category_counter[condition.get("category", "General")] += 1
        else:
            category_counter[entry.get("top_category", "General")] += 1

    medium_high_total = sum(
        int(entry.get("medium_high_condition_count", 0) or 0)
        for entry in history_entries[:5]
    )
    health_score = max(0, min(100, 100 - (medium_high_total * 5)))
    streak = compute_check_streak(history_entries)
    most_common = symptom_counter.most_common(1)
    last_check_date = format_datetime_label(
        (history_entries[0] if history_entries else {}).get("date")
    )

    return {
        "symptom_counts": [
            {"label": label.title(), "count": count}
            for label, count in symptom_counter.most_common(8)
        ],
        "category_breakdown": {
            key: category_counter.get(key, 0)
            for key in [
                "Respiratory",
                "Digestive",
                "Neurological",
                "Musculoskeletal",
                "General",
            ]
        },
        "health_score": health_score,
        "streak": streak,
        "total_checks": len(history_entries),
        "most_common_symptom": most_common[0][0].title() if most_common else "No data",
        "last_check_date": last_check_date if history_entries else "No checks yet",
    }


def build_pdf_report(check_result):
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f5ea8"),
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportBody",
            parent=styles["BodyText"],
            fontSize=10.5,
            leading=14,
            spaceAfter=6,
        )
    )

    patient = check_result.get("patient", {})
    condition_details = check_result.get("condition_details", [])[:3]
    treatment_points = ordered_unique(
        (check_result.get("remedies") or [])
        + (check_result.get("lifestyle_suggestions") or [])
    )[:8]

    elements = [
        Paragraph(
            "Health Checker Pro - Symptom Analysis Report",
            styles["ReportTitle"],
        ),
        Paragraph(
            f"Patient: Age {patient.get('age', 'N/A')} | Gender {format_gender(patient.get('gender'))}",
            styles["ReportBody"],
        ),
        Paragraph(
            f"Date & Time: {format_datetime_label(check_result.get('checked_at'))}",
            styles["ReportBody"],
        ),
        Spacer(1, 8),
        Paragraph("Symptoms Selected", styles["Heading3"]),
        ListFlowable(
            [
                ListItem(Paragraph(symptom.title(), styles["ReportBody"]))
                for symptom in check_result.get("selected_symptoms", [])
            ],
            bulletType="bullet",
        ),
        Spacer(1, 10),
        Paragraph("Top Condition Matches", styles["Heading3"]),
    ]

    table_data = [["Condition", "Confidence", "Urgency"]]
    for condition in condition_details:
        table_data.append(
            [
                condition.get("name", "Unknown"),
                f"{condition.get('confidence', 0)}%",
                condition.get("urgency", "low").capitalize(),
            ]
        )
    if len(table_data) == 1:
        table_data.append(["No clear match", "-", "-"])

    table = Table(table_data, colWidths=[240, 100, 100])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f5ea8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d5dfeb")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.whitesmoke, colors.HexColor("#edf4fb")],
                ),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.extend(
        [
            table,
            Spacer(1, 12),
            Paragraph("Treatment & Precautions", styles["Heading3"]),
            ListFlowable(
                [
                    ListItem(
                        Paragraph(strip_icon_prefix(item), styles["ReportBody"])
                    )
                    for item in treatment_points
                ]
                or [
                    ListItem(
                        Paragraph("No treatment guidance saved.", styles["ReportBody"])
                    )
                ],
                bulletType="bullet",
            ),
            Spacer(1, 12),
            Paragraph(
                "This is not a medical diagnosis. Consult a licensed physician.",
                styles["Italic"],
            ),
        ]
    )

    document.build(elements)
    buffer.seek(0)
    return buffer


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

    @app.route("/api/history-stats")
    @login_required
    def history_stats():
        email = normalize_email(session.get("email"))
        history = get_history_entries(email) if email else []
        return jsonify(build_history_stats(history))

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("10 per minute", methods=["POST"])
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
                time.sleep(0.4)
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
            elif len(password) < 8:
                flash("Use at least 8 characters for password.", "danger")
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

        current_result = get_current_check_result() or {}
        selected_symptoms = current_result.get("selected_symptoms", [])
        symptom_categories = get_symptom_categories()
        return render_template(
            "symptoms.html",
            current_step="symptoms",
            show_steps=True,
            show_sidebar=True,
            sidebar=checker_sidebar_context(),
            symptom_names=get_searchable_symptoms(),
            selected_symptoms=selected_symptoms,
            symptom_categories=symptom_categories,
            symptom_results=build_symptom_result_items(
                selected_symptoms=selected_symptoms
            ),
            symptom_zone_map=SYMPTOM_ZONE_MAP,
            body_zone_targets=BODY_ZONE_TARGETS,
        )

    @app.route("/search-symptoms")
    @login_required
    def search_symptoms():
        query = request.args.get("q", "")
        zone = request.args.get("zone", "")
        selected = request.args.getlist("symptoms")
        items = build_symptom_result_items(
            query=query,
            zone=zone,
            selected_symptoms=selected,
        )
        return render_template(
            SYMPTOM_RESULTS_TEMPLATE,
            symptom_results=items,
            empty_message="No symptoms found. Try a broader search.",
        )

    @app.route("/conditions")
    @login_required
    def conditions():
        if not has_profile():
            return redirect(url_for("info"))

        result = get_current_check_result()
        if not result:
            flash("No analysis found yet. Please select symptoms first.", "warning")
            return redirect(url_for("symptoms"))

        condition_details = result.get("condition_details", [])
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
            predicted_disease=result.get("predicted_disease", "No clear match"),
            analysis=result.get("analysis", {}),
            selected_symptoms=result.get("selected_symptoms", []),
            current_check_id=result.get("id"),
            check_result=result,
            high_urgency_present=any(
                condition.get("urgency") == "high" for condition in condition_details
            ),
        )

    @app.route("/details/<path:condition_name>")
    @login_required
    def details(condition_name):
        if not has_profile():
            return redirect(url_for("info"))

        result = get_current_check_result()
        if not result:
            return redirect(url_for("symptoms"))

        condition = get_condition_from_result(result, condition_name)
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

        result = get_current_check_result()
        if not result:
            return redirect(url_for("symptoms"))

        condition = get_condition_from_result(result, condition_name)
        if not condition:
            return redirect(url_for("conditions"))

        session["active_condition"] = condition.get("name", "")
        emergency_detected = bool(result.get("emergency_detected"))
        emergency_message = result.get("emergency_message", "")
        when_to_see_doctor = list(get_condition_precautions(condition))

        if emergency_detected and emergency_message:
            when_to_see_doctor.insert(0, emergency_message)

        lifestyle_suggestions = result.get("lifestyle_suggestions", [])
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
            remedies=result.get("remedies", []),
            emergency_detected=emergency_detected,
            emergency_message=emergency_message,
            when_to_see_doctor=ordered_unique(when_to_see_doctor),
            lifestyle_suggestions=lifestyle_suggestions,
            current_check_id=result.get("id"),
            check_result=result,
        )

    @app.route("/report/<int:check_id>/pdf")
    @login_required
    def download_report(check_id):
        email = normalize_email(session.get("email"))
        check_result = get_check_result(email, check_id) if email else None
        if not check_result:
            flash("Report not found for this check.", "warning")
            return redirect(url_for("conditions"))

        pdf_buffer = build_pdf_report(check_result)
        filename = f"health-check-report-{check_id}.pdf"
        return Response(
            pdf_buffer.getvalue(),
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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
        stats = build_history_stats(history)
        return render_template(
            "profile.html",
            history=history,
            stats=stats,
            email=email,
            show_steps=False,
            show_sidebar=False,
        )

    @app.route("/profile/export-csv")
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
            herbals = [item for item in remedies if item.startswith("🌿")]
            dietary = [
                item
                for item in remedies
                if item.startswith(("🥕", "🍎", "🍌", "🍚", "🥬"))
            ]
            lifestyle = [
                item for item in remedies if item.startswith(("🧘", "😴", "🛌", "👁️"))
            ]
            liquids = [
                item
                for item in remedies
                if item.startswith(("💧", "🫐", "🥛", "🍵", "🍋"))
            ]
            other = [
                item
                for item in remedies
                if item not in herbals + dietary + lifestyle + liquids
            ]

            remedy_sections = []
            if herbals:
                cleaned_herbs = [strip_icon_prefix(item) for item in herbals]
                if len(cleaned_herbs) > 1:
                    remedy_sections.append(
                        f"🌿 **Ayurvedic Herbal Remedies**: {', '.join(cleaned_herbs[:-1])} and {cleaned_herbs[-1]}."
                    )
                else:
                    remedy_sections.append(
                        f"🌿 **Ayurvedic Herbal Remedies**: {cleaned_herbs[0]}."
                    )

            if dietary:
                foods_text = ", ".join(strip_icon_prefix(item) for item in dietary)
                remedy_sections.append(
                    f"🍎 **Dietary Recommendations**: Incorporate {foods_text} into your meals."
                )

            if lifestyle:
                lifestyle_text = ", ".join(
                    strip_icon_prefix(item) for item in lifestyle
                )
                remedy_sections.append(f"🧘 **Lifestyle & Rest**: {lifestyle_text}.")

            if liquids:
                liquids_text = ", ".join(strip_icon_prefix(item) for item in liquids)
                remedy_sections.append(f"💧 **Hydration**: {liquids_text}.")

            if other:
                remedy_sections.extend(other)

            remedies = [" ".join(remedy_sections)] if remedy_sections else remedies
            lifestyle_suggestions = ordered_unique(
                strip_icon_prefix(item) for item in lifestyle + liquids + dietary
            )[:8]

        condition_details = compute_condition_matches(
            selected_symptoms, age, gender, form_data
        )
        predicted_disease = predict_disease(selected_symptoms)

        if predicted_disease and predicted_disease not in {
            "No clear match",
            "Prediction Error",
            "No clear match (Model not loaded)",
        }:
            existing = next(
                (
                    condition
                    for condition in condition_details
                    if condition["name"].lower() == predicted_disease.lower()
                ),
                None,
            )
            if not existing:
                ml_condition = {
                    "name": predicted_disease,
                    "confidence": 95,
                    "match_label": "Machine Learning Match",
                    "urgency": "medium",
                    "severity": "medium",
                    "evidence": ["statistical pattern matching"],
                    "description": (
                        "This condition was predicted by our trained Random Forest "
                        "model based on your symptom profile."
                    ),
                }
                condition_details.insert(0, ml_condition)
            else:
                condition_details.remove(existing)
                existing["match_label"] = "Verified by Machine Learning"
                existing["confidence"] = min(99, existing["confidence"] + 20)
                condition_details.insert(0, existing)

        for condition in condition_details:
            condition["possible_causes"] = condition.get("evidence", [])
            condition["precautions"] = get_condition_precautions(condition)
            condition["category"] = classify_condition(condition)

        emergency_detected, emergency_message = detect_emergency_signals(
            selected_symptoms, form_data
        )

        quality = "good"
        suggestion = "Results confidence improves when you add specific symptom details."
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

        checked_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        top_condition = condition_details[0] if condition_details else {}
        medium_high_condition_count = sum(
            1
            for condition in condition_details
            if condition.get("urgency") in {"medium", "high"}
        )
        check_result = {
            "checked_at": checked_at,
            "selected_symptoms": selected_symptoms,
            "predicted_disease": predicted_disease,
            "condition_details": condition_details,
            "remedies": remedies,
            "emergency_detected": emergency_detected,
            "emergency_message": emergency_message,
            "analysis": {
                "symptom_count": len(selected_symptoms),
                "quality": quality,
                "suggestion": suggestion,
            },
            "lifestyle_suggestions": lifestyle_suggestions,
            "patient": {"age": age, "gender": gender},
        }

        email = normalize_email(session.get("email"))
        check_id = None
        if email:
            check_id = save_check_result(email, check_result)
            history_entry = {
                "date": checked_at,
                "checked_at": checked_at,
                "check_id": check_id,
                "symptoms": selected_symptoms,
                "conditions": [condition["name"] for condition in condition_details[:3]],
                "condition_summaries": [
                    {
                        "name": condition["name"],
                        "urgency": condition["urgency"],
                        "confidence": condition["confidence"],
                        "category": condition["category"],
                    }
                    for condition in condition_details[:3]
                ],
                "top_condition": top_condition.get("name", "No clear match"),
                "top_urgency": top_condition.get("urgency", "low"),
                "top_category": top_condition.get("category", "General"),
                "remedies": remedies,
                "analysis_quality": quality,
                "medium_high_condition_count": medium_high_condition_count,
            }
            save_history_entry(email, history_entry, check_result_id=check_id)

        session["last_check_id"] = check_id
        if condition_details:
            session["active_condition"] = condition_details[0]["name"]

        flash("Prediction completed. Review your condition matches.", "success")
        return redirect(url_for("conditions"))
