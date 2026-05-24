"""Core symptom-checker workflow: info → symptoms → check → conditions → details → treatment."""

import logging
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from predictor import predict_disease

from app.models.user_store import (
    normalize_email,
    save_check_result,
    save_history_entry,
    update_user_profile,
)
from app.routes.helpers import (
    BODY_ZONE_TARGETS,
    SYMPTOM_RESULTS_TEMPLATE,
    SYMPTOM_ZONE_MAP,
    VALID_GENDERS,
    build_symptom_result_items,
    checker_sidebar_context,
    clean_text,
    clear_checker_session,
    get_condition_from_result,
    get_current_check_result,
    get_profile_from_session,
    has_profile,
    login_required,
)
from app.services.chatbot_service import extract_symptoms_from_text
from app.services.check_service import (
    assess_quality,
    build_check_result,
    build_remedies,
    enrich_conditions,
    merge_ml_prediction,
)
from app.services.prediction_service import (
    compute_condition_matches,
    detect_emergency_signals,
    get_condition_precautions,
    get_searchable_symptoms,
    get_symptom_categories,
    normalize_symptom_name,
    ordered_unique,
)
from app.services.shap_service import get_local_shap_explanation

logger = logging.getLogger(__name__)

checker_bp = Blueprint("checker", __name__)


@checker_bp.route("/info", methods=["GET", "POST"])
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
            return redirect(url_for("checker.symptoms"))

    return render_template(
        "info.html",
        current_step="info",
        show_steps=True,
        show_sidebar=True,
        sidebar=checker_sidebar_context(),
        age=form_age,
        gender=form_gender,
    )


@checker_bp.route("/symptoms")
@login_required
def symptoms():
    if not has_profile():
        flash("Please complete your profile first.", "warning")
        return redirect(url_for("checker.info"))

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


@checker_bp.route("/search-symptoms")
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


@checker_bp.route("/api/chat", methods=["POST"])
@login_required
def chat_api():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "No message provided"}), 400

    message = data['message']
    extracted_symptoms = extract_symptoms_from_text(message)

    if not extracted_symptoms:
        return jsonify({
            "reply": "I couldn't clearly detect any symptoms from that. Could you describe how you're feeling using different words?",
            "symptoms": []
        })

    symptom_list = ", ".join(extracted_symptoms)
    reply = f"I detected these symptoms: {symptom_list}. I have selected them for you below!"
    return jsonify({
        "reply": reply,
        "symptoms": extracted_symptoms
    })


@checker_bp.route("/check", methods=["POST"])
@login_required
def check_symptoms():
    if not has_profile():
        flash("Please complete your profile first.", "warning")
        return redirect(url_for("checker.info"))

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
        return redirect(url_for("checker.symptoms"))

    age, gender = get_profile_from_session()
    form_data = {
        key: clean_text(request.form.get(key), max_length=80)
        for key in request.form.keys()
    }
    cough_type = (form_data.get("cough_type") or "").lower()

    remedies, lifestyle_suggestions = build_remedies(selected_symptoms)

    condition_details = compute_condition_matches(
        selected_symptoms, age, gender, form_data
    )
    predicted_disease = predict_disease(selected_symptoms)
    ml_degraded = predicted_disease in {"Prediction Error", "No clear match (Model not loaded)"}

    # --- Explainable AI: compute SHAP feature importance ---
    shap_data = get_local_shap_explanation(selected_symptoms)

    condition_details = merge_ml_prediction(condition_details, predicted_disease)
    condition_details = enrich_conditions(condition_details)

    emergency_detected, emergency_message = detect_emergency_signals(
        selected_symptoms, form_data
    )

    quality, suggestion = assess_quality(selected_symptoms, cough_type)

    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    top_condition = condition_details[0] if condition_details else {}
    medium_high_condition_count = sum(
        1
        for condition in condition_details
        if condition.get("urgency") in {"medium", "high"}
    )
    check_result = build_check_result(
        checked_at=checked_at,
        selected_symptoms=selected_symptoms,
        predicted_disease=predicted_disease,
        condition_details=condition_details,
        remedies=remedies,
        emergency_detected=emergency_detected,
        emergency_message=emergency_message,
        quality=quality,
        suggestion=suggestion,
        lifestyle_suggestions=lifestyle_suggestions,
        age=age,
        gender=gender,
        shap_data=shap_data,
    )

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
    # Guest fallback: store result directly in session so conditions page
    # can always render SHAP panel and results without a DB lookup
    if not email:
        # Exclude shap_data from session (too large); store flag only
        slim = {k: v for k, v in check_result.items() if k != "shap_data"}
        slim["shap_data"] = check_result.get("shap_data", {"available": False})
        session["guest_check_result"] = slim

    if condition_details:
        session["active_condition"] = condition_details[0]["name"]

    if ml_degraded:
        flash("ML prediction service was unavailable. Results are based on the rule engine only.", "warning")
    flash("Prediction completed. Review your condition matches.", "success")
    return redirect(url_for("checker.conditions"))



@checker_bp.route("/conditions")
@login_required
def conditions():
    if not has_profile():
        return redirect(url_for("checker.info"))

    result = get_current_check_result()
    if not result:
        flash("No analysis found yet. Please select symptoms first.", "warning")
        return redirect(url_for("checker.symptoms"))

    condition_details = result.get("condition_details", [])
    if not condition_details:
        flash("No analysis found yet. Please select symptoms first.", "warning")
        return redirect(url_for("checker.symptoms"))

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
        shap_data=result.get("shap_data", {"available": False}),
        high_urgency_present=any(
            condition.get("urgency") == "high" for condition in condition_details
        ),
    )


@checker_bp.route("/details/<path:condition_name>")
@login_required
def details(condition_name):
    if not has_profile():
        return redirect(url_for("checker.info"))

    result = get_current_check_result()
    if not result:
        return redirect(url_for("checker.symptoms"))

    condition = get_condition_from_result(result, condition_name)
    if not condition:
        flash("Condition not found in the current analysis.", "warning")
        return redirect(url_for("checker.conditions"))

    session["active_condition"] = condition.get("name", "")
    return render_template(
        "details.html",
        current_step="details",
        show_steps=True,
        show_sidebar=True,
        sidebar=checker_sidebar_context(),
        condition=condition,
    )


@checker_bp.route("/treatment/<path:condition_name>")
@login_required
def treatment(condition_name):
    if not has_profile():
        return redirect(url_for("checker.info"))

    result = get_current_check_result()
    if not result:
        return redirect(url_for("checker.symptoms"))

    condition = get_condition_from_result(result, condition_name)
    if not condition:
        return redirect(url_for("checker.conditions"))

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


@checker_bp.route("/start-over")
@login_required
def start_over():
    clear_checker_session()
    session.pop("patient_age", None)
    session.pop("patient_gender", None)
    flash("Started a new check session.", "info")
    return redirect(url_for("checker.info"))
