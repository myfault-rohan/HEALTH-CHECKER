"""Shared helpers, constants, and decorators used across route blueprints."""

import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from functools import wraps

from flask import flash, jsonify, redirect, request, session, url_for
from markupsafe import Markup, escape

from app.models.user_store import (
    get_check_result,
    get_latest_check_result,
    normalize_email,
)
from app.services.prediction_service import (
    SYMPTOM_ALIASES,
    get_searchable_symptoms,
    get_symptom_categories,
    normalize_symptom_name,
    ordered_unique,
    symptoms_conditions,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_GENDERS = {"male", "female", "other"}
CHECKER_SESSION_KEYS = ["last_check_id", "active_condition"]

ICON_PREFIXES = [
    "🌿", "💧", "😴", "🛌", "🧘", "🍎", "🍌", "🍚", "🥕", "🥬",
    "🫐", "🥛", "👁️", "🍵", "🚫", "🦶", "🛁", "🥵", "🧊", "🍋", "👕",
]

SYMPTOM_ZONE_MAP = {
    "head": ["headache", "dizziness", "blurred vision", "confusion"],
    "chest": [
        "chest pain", "shortness of breath", "wheezing",
        "palpitations", "cough", "cold",
    ],
    "abdomen": [
        "abdominal pain", "nausea", "vomiting",
        "diarrhea", "bloating", "heartburn",
    ],
    "arms": ["joint pain", "muscle pain", "swelling", "stiffness"],
    "legs": ["joint pain", "muscle pain", "swelling", "stiffness"],
    "full-body": ["fever", "fatigue", "chills", "weight loss", "insomnia", "stress"],
}

BODY_ZONE_TARGETS = {
    "head": "category-neurological",
    "chest": "category-respiratory",
    "abdomen": "category-digestive",
    "arms": "category-musculoskeletal",
    "legs": "category-musculoskeletal",
    "full-body": "category-general",
}

SYMPTOM_META = {
    # Respiratory
    "cough": {"cat": "respiratory", "icon": "fa-head-side-cough", "emoji": "🗣️"},
    "cold": {"cat": "respiratory", "icon": "fa-snowflake", "emoji": "🤧"},
    "shortness of breath": {"cat": "respiratory", "icon": "fa-lungs", "emoji": "🫁"},
    "chest pain": {"cat": "respiratory", "icon": "fa-heart-pulse", "emoji": "💔"},
    "wheezing": {"cat": "respiratory", "icon": "fa-wind", "emoji": "😮‍💨"},
    "sore throat": {"cat": "respiratory", "icon": "fa-head-side-virus", "emoji": "🧣"},
    "runny nose": {"cat": "respiratory", "icon": "fa-box-tissue", "emoji": "👃"},
    "sneezing": {"cat": "respiratory", "icon": "fa-face-rolling-eyes", "emoji": "🤧"},
    "congestion": {"cat": "respiratory", "icon": "fa-head-side", "emoji": "😮‍💨"},
    # Digestive
    "abdominal pain": {"cat": "digestive", "icon": "fa-circle-dot", "emoji": "🫄"},
    "stomach pain": {"cat": "digestive", "icon": "fa-circle-dot", "emoji": "😣"},
    "nausea": {"cat": "digestive", "icon": "fa-face-frown", "emoji": "🤢"},
    "vomiting": {"cat": "digestive", "icon": "fa-toilet", "emoji": "🤮"},
    "diarrhea": {"cat": "digestive", "icon": "fa-water", "emoji": "💧"},
    "constipation": {"cat": "digestive", "icon": "fa-stop", "emoji": "🧱"},
    "bloating": {"cat": "digestive", "icon": "fa-circle-half-stroke", "emoji": "🎈"},
    "heartburn": {"cat": "digestive", "icon": "fa-fire", "emoji": "🔥"},
    "acidity": {"cat": "digestive", "icon": "fa-lemon", "emoji": "🍋"},
    "loss of appetite": {"cat": "digestive", "icon": "fa-utensils", "emoji": "🍽️"},
    "urinary problems": {"cat": "digestive", "icon": "fa-droplet", "emoji": "🚽"},
    # Neurological
    "headache": {"cat": "neurological", "icon": "fa-brain", "emoji": "🤕"},
    "dizziness": {"cat": "neurological", "icon": "fa-compass", "emoji": "🌀"},
    "blurred vision": {"cat": "neurological", "icon": "fa-eye-low-vision", "emoji": "👁️"},
    "confusion": {"cat": "neurological", "icon": "fa-question", "emoji": "❓"},
    "insomnia": {"cat": "neurological", "icon": "fa-moon", "emoji": "🌙"},
    "fatigue": {"cat": "neurological", "icon": "fa-bolt", "emoji": "⚡"},
    "chills": {"cat": "neurological", "icon": "fa-icicles", "emoji": "🥶"},
    "stress": {"cat": "neurological", "icon": "fa-burst", "emoji": "🤯"},
    "palpitations": {"cat": "neurological", "icon": "fa-heartbeat", "emoji": "💓"},
    # Musculoskeletal
    "joint pain": {"cat": "musculoskeletal", "icon": "fa-bone", "emoji": "🦴"},
    "back pain": {"cat": "musculoskeletal", "icon": "fa-person", "emoji": "🧍"},
    "muscle pain": {"cat": "musculoskeletal", "icon": "fa-dumbbell", "emoji": "💪"},
    "stiffness": {"cat": "musculoskeletal", "icon": "fa-lock", "emoji": "🔒"},
    "leg pain": {"cat": "musculoskeletal", "icon": "fa-shoe-prints", "emoji": "🦵"},
    "waist pain": {"cat": "musculoskeletal", "icon": "fa-arrows-left-right", "emoji": "🚶"},
    "body weakness": {"cat": "musculoskeletal", "icon": "fa-battery-quarter", "emoji": "🪫"},
    "swelling": {"cat": "musculoskeletal", "icon": "fa-expand", "emoji": "💧"},
    # General
    "fever": {"cat": "general", "icon": "fa-temperature-high", "emoji": "🌡️"},
    "dehydration": {"cat": "general", "icon": "fa-glass-water", "emoji": "🥤"},
    "menstrual pain": {"cat": "general", "icon": "fa-calendar-day", "emoji": "🩸"},
    "night sweats": {"cat": "general", "icon": "fa-bed", "emoji": "💦"},
    "nightfall": {"cat": "general", "icon": "fa-cloud-moon", "emoji": "🌌"},
    "rash": {"cat": "general", "icon": "fa-hand-dots", "emoji": "🔴"},
    "watery eyes": {"cat": "general", "icon": "fa-eye", "emoji": "🥺"},
    "weight loss": {"cat": "general", "icon": "fa-weight-scale", "emoji": "⚖️"},
}

POPULAR_SYMPTOMS = [
    {"name": "fever", "label": "Fever", "icon": "fa-temperature-high", "emoji": "🌡️"},
    {"name": "cough", "label": "Cough", "icon": "fa-head-side-cough", "emoji": "🗣️"},
    {"name": "headache", "label": "Headache", "icon": "fa-brain", "emoji": "🤕"},
    {"name": "sore throat", "label": "Sore Throat", "icon": "fa-head-side-virus", "emoji": "🧣"},
    {"name": "shortness of breath", "label": "Shortness of Breath", "icon": "fa-lungs", "emoji": "🫁"},
    {"name": "fatigue", "label": "Fatigue", "icon": "fa-bolt", "emoji": "⚡"},
    {"name": "chest pain", "label": "Chest Pain", "icon": "fa-heart-pulse", "emoji": "💔"},
    {"name": "nausea", "label": "Nausea", "icon": "fa-face-frown", "emoji": "🤢"},
    {"name": "joint pain", "label": "Joint Pain", "icon": "fa-bone", "emoji": "🦴"},
    {"name": "cold", "label": "Cold", "icon": "fa-snowflake", "emoji": "🤧"},
    {"name": "stomach pain", "label": "Stomach Pain", "icon": "fa-circle-dot", "emoji": "🫄"},
    {"name": "dizziness", "label": "Dizziness", "icon": "fa-compass", "emoji": "🌀"},
]

CATEGORY_TABS = [
    {"id": "all", "label": "All", "icon": "fa-border-all", "emoji": "🌐", "count": 45},
    {"id": "neurological", "label": "Head & Mind", "icon": "fa-brain", "emoji": "🧠", "count": 9},
    {"id": "respiratory", "label": "Lungs & Chest", "icon": "fa-lungs", "emoji": "🫁", "count": 9},
    {"id": "digestive", "label": "Stomach & Digestion", "icon": "fa-virus", "emoji": "🫄", "count": 11},
    {"id": "musculoskeletal", "label": "Joints & Muscles", "icon": "fa-bone", "emoji": "🦴", "count": 8},
    {"id": "general", "label": "General", "icon": "fa-heart-pulse", "emoji": "🩹", "count": 8},
]

CATEGORY_KEYWORDS = {
    "Respiratory": [
        "cold", "cough", "flu", "sinus", "bronch",
        "asthma", "breath", "throat", "respir", "wheez",
    ],
    "Digestive": [
        "digest", "stomach", "acid", "abdominal", "bowel",
        "constipation", "diarrhea", "vomit", "nausea", "heartburn", "uti",
    ],
    "Neurological": [
        "headache", "migraine", "vertigo", "vision", "confusion",
        "anxiety", "insomnia", "dehydration", "fatigue", "stress",
    ],
    "Musculoskeletal": [
        "joint", "muscle", "strain", "back",
        "swelling", "stiffness", "arthritis",
    ],
}

SYMPTOM_RESULTS_TEMPLATE = "_symptom_results.html"


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "logged_in" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized"}), 401
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped


def is_doctor(email):
    if not email:
        return False
    email_lower = email.lower()
    return (
        email_lower.endswith("@clinic.com") or
        email_lower.endswith("@hospital.com") or
        email_lower.endswith("@healthchecker.com") or
        email_lower.startswith("doctor.") or
        email_lower.startswith("dr.")
    )


def doctor_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        email = normalize_email(session.get("email"))
        if not is_doctor(email):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Forbidden - Clinician access required"}), 403
            flash("Access denied. Doctor / Clinician portal requires authorized credentials.", "danger")
            return redirect(url_for("dashboard.dashboard"))
        return view_func(*args, **kwargs)

    return wrapped



# ---------------------------------------------------------------------------
# Text / formatting utilities
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

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
        # Guest user — return result stored directly in session
        return session.get("guest_check_result")

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


# ---------------------------------------------------------------------------
# Symptom search helpers
# ---------------------------------------------------------------------------

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
        lambda match: f"<strong>{match.group(0)}</strong>", str(label)
    )
    return Markup(highlighted)


def build_symptom_result_items(query="", zone="", category="", selected_symptoms=None):
    query = clean_text(query, max_length=50).lower()
    zone = clean_text(zone, max_length=20).lower()
    category = clean_text(category, max_length=30).lower()
    selected_set = {normalize_symptom_name(item) for item in (selected_symptoms or [])}
    canonical_list = sorted(symptoms_conditions.keys())

    # Category / Zone filtering
    if category and category != "all":
        cat_map = get_symptom_categories()
        allowed = set(cat_map.get(category, []))
        pool = [item for item in canonical_list if item in allowed]
    elif zone and zone in SYMPTOM_ZONE_MAP:
        allowed = set(SYMPTOM_ZONE_MAP[zone])
        pool = [item for item in canonical_list if item in allowed]
    else:
        pool = canonical_list

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

            # Check if query or tokens match an alias for this symptom
            alias_match = False
            for alias_key, canonical_target in SYMPTOM_ALIASES.items():
                if canonical_target == symptom and (
                    query in alias_key or any(tok in alias_key for tok in query_tokens)
                ):
                    alias_match = True
                    break

            if token_matches == 0 and not alias_match:
                continue

            score = token_matches * 10 + prefix_matches * 6
            if text.startswith(query):
                score += 20
            elif query in text:
                score += 8
            if len(query_tokens) > 1 and token_matches == len(query_tokens):
                score += 12
            if alias_match:
                score += 15

            scored_pool.append((score, len(text), symptom))

        pool = [symptom for _, _, symptom in sorted(scored_pool, key=lambda item: (-item[0], item[1], item[2]))]

    items = []
    for symptom in pool:
        meta = SYMPTOM_META.get(
            symptom, {"cat": "general", "icon": "fa-circle-dot", "emoji": "🩺"}
        )
        items.append(
            {
                "id": f"symptom-choice-{symptom.replace(' ', '-')}",
                "value": symptom,
                "name": symptom.title(),
                "category": meta["cat"],
                "icon": meta["icon"],
                "emoji": meta["emoji"],
                "checked": symptom in selected_set,
                "highlighted_name": highlight_match(symptom.title(), query),
            }
        )
    return items


# ---------------------------------------------------------------------------
# Condition classification
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# History / stats
# ---------------------------------------------------------------------------

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
