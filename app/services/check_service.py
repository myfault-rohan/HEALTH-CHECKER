from app.services.disease_kb import get_ayurvedic_remedies, get_description
from app.services.disease_kb import get_precautions as kb_precautions
from app.services.prediction_service import (
    get_condition_precautions,
    ordered_unique,
    symptoms_conditions,
)


def build_remedies(selected_symptoms):
    """Build, categorize, and format remedies list."""
    from app.routes.helpers import strip_icon_prefix
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
    return remedies, lifestyle_suggestions


def merge_ml_prediction(condition_details, predicted_disease):
    """Merge ML prediction into rule engine condition matches."""
    condition_details = list(condition_details)
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
                    "This condition was predicted by our HistGradientBoosting "
                    "ML model trained on symptom-condition correlation patterns."
                ),
            }
            condition_details.insert(0, ml_condition)
        else:
            condition_details.remove(existing)
            existing["match_label"] = "Verified by Machine Learning"
            existing["confidence"] = min(99, existing["confidence"] + 20)
            condition_details.insert(0, existing)
    return condition_details


def enrich_conditions(condition_details):
    """Enrich conditions with database description, ayurvedic remedies, and precautions."""
    from app.routes.helpers import classify_condition
    from app.services.prediction_service import CONDITION_DESCRIPTIONS
    enriched = []
    for cond in condition_details:
        condition = dict(cond)
        condition["possible_causes"] = condition.get("evidence", [])
        cname = condition.get("name", "")
        kb_desc = get_description(cname)
        if kb_desc and not condition.get("description"):
            condition["description"] = kb_desc
        elif not condition.get("description"):
            condition["description"] = CONDITION_DESCRIPTIONS.get(cname, "Pattern inferred from your selected symptoms.")
        condition["ayurvedic_remedies"] = get_ayurvedic_remedies(cname)
        kb_prec = kb_precautions(cname)
        condition["precautions"] = kb_prec if kb_prec else get_condition_precautions(condition)
        condition["category"] = classify_condition(condition)
        enriched.append(condition)
    return enriched


def assess_quality(selected_symptoms, cough_type):
    """Assess input quality and provide suggestion."""
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
    return quality, suggestion


def build_check_result(
    checked_at,
    selected_symptoms,
    predicted_disease,
    condition_details,
    remedies,
    emergency_detected,
    emergency_message,
    quality,
    suggestion,
    lifestyle_suggestions,
    age,
    gender,
    shap_data,
):
    """Assemble the final check result payload."""
    return {
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
        "shap_data": shap_data,
    }
