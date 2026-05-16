# -*- coding: utf-8 -*-
"""SHAP Explainability Service.

Calls the ML microservice /explain endpoint and returns structured
feature-importance data ready for template rendering.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8000")

# Friendly display names for the raw feature columns
FEATURE_DISPLAY_NAMES = {
    "headache": "Headache",
    "dizziness": "Dizziness",
    "blurred_vision": "Blurred Vision",
    "confusion": "Confusion",
    "cough": "Cough",
    "shortness_of_breath": "Shortness of Breath",
    "chest_pain": "Chest Pain",
    "wheezing": "Wheezing",
    "palpitations": "Palpitations",
    "abdominal_pain": "Abdominal Pain",
    "nausea": "Nausea",
    "vomiting": "Vomiting",
    "diarrhea": "Diarrhea",
    "constipation": "Constipation",
    "bloating": "Bloating",
    "heartburn": "Heartburn",
    "urinary_problems": "Urinary Problems",
    "fever": "Fever",
    "fatigue": "Fatigue",
    "chills": "Chills",
    "night_sweats": "Night Sweats",
    "weight_loss": "Weight Loss",
    "insomnia": "Insomnia",
    "loss_of_appetite": "Loss of Appetite",
    "sore_throat": "Sore Throat",
    "runny_nose": "Runny Nose",
    "sneezing": "Sneezing",
    "congestion": "Congestion",
    "rash": "Rash",
    "swelling": "Swelling",
    "joint_pain": "Joint Pain",
    "back_pain": "Back Pain",
    "muscle_pain": "Muscle Pain",
    "stiffness": "Stiffness",
    "acidity": "Acidity",
    "leg_pain": "Leg Pain",
    "body_weakness": "Body Weakness",
    "stomach_pain": "Stomach Pain",
    "waist_pain": "Waist Pain",
    "watery_eyes": "Watery Eyes",
    "nightfall": "Night Disturbances",
    "menstrual_pain": "Menstrual Pain",
    "dehydration": "Dehydration",
    "cold": "Cold",
    "stress": "Stress",
}


def get_shap_explanation(symptoms: list[str]) -> dict | None:
    """Fetch SHAP feature-importance values from the ML microservice.

    Returns a dict with keys:
      - ``predicted_disease``  – top predicted class
      - ``features``           – list of dicts: {name, display_name, value, shap_value, direction}
      - ``base_value``         – model base (expected) value
      - ``available``          – True if explanation was successfully computed

    Returns ``None`` (and logs a warning) if the service is unreachable.
    """
    if not symptoms:
        return _unavailable()

    try:
        response = requests.post(
            f"{ML_SERVICE_URL}/explain",
            json={"symptoms": symptoms},
            timeout=8,
        )
        if response.status_code != 200:
            logger.warning("SHAP service returned %s", response.status_code)
            return _unavailable()

        data = response.json()
        return _format_explanation(data)

    except requests.exceptions.ConnectionError:
        logger.warning("ML service offline — SHAP unavailable")
        return _unavailable()
    except Exception:
        logger.exception("Unexpected error fetching SHAP explanation")
        return _unavailable()


# ---------------------------------------------------------------------------
# Fallback: local SHAP when ML microservice is offline
# ---------------------------------------------------------------------------

def get_local_shap_explanation(symptoms: list[str]) -> dict:
    """Compute SHAP values locally without the microservice.

    Used as a fallback when the FastAPI ML service is unreachable. Loads
    the model directly from disk and computes TreeExplainer in-process.
    """
    if not symptoms:
        return _unavailable()

    import pickle
    import numpy as np
    import pandas as pd

    try:
        import shap  # noqa: F401
    except ImportError:
        logger.warning("shap not installed — explainability unavailable")
        return _unavailable()

    model_path = os.path.join(os.path.dirname(__file__), "..", "..", "model", "model.pkl")
    model_path = os.path.normpath(model_path)

    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
    except FileNotFoundError:
        logger.warning("model.pkl not found at %s", model_path)
        return _unavailable()
    except Exception:
        logger.exception("Failed to load model for local SHAP")
        return _unavailable()

    features = list(FEATURE_DISPLAY_NAMES.keys())

    # Build binary feature vector
    selected_normalized = {s.strip().lower().replace(" ", "_") for s in symptoms}
    vector = [1 if f in selected_normalized else 0 for f in features]
    input_df = pd.DataFrame([vector], columns=features)

    try:
        import shap as shap_lib
        import numpy as np

        explainer = shap_lib.TreeExplainer(model)
        shap_values = explainer.shap_values(input_df)  # shape: (n_samples, n_features, n_classes)

        predicted_class = model.predict(input_df)[0]
        predicted_disease = str(predicted_class).replace("_", " ")

        classes = model.classes_.tolist()
        try:
            class_idx = classes.index(predicted_class)
        except ValueError:
            class_idx = 0

        sv_array = np.array(shap_values)

        # Handle all known SHAP output shapes from HistGradientBoostingClassifier
        if sv_array.ndim == 3:
            # Shape: (n_samples, n_features, n_classes) — standard for multi-class
            sv = sv_array[0, :, class_idx]
        elif sv_array.ndim == 2:
            # Shape: (n_samples, n_features) — binary classifier
            sv = sv_array[0]
        elif isinstance(shap_values, list):
            # Older SHAP: list of [n_samples, n_features] per class
            sv = np.array(shap_values[class_idx])[0]
        else:
            sv = sv_array.flatten()[:len(features)]

        # Extract scalar base value for the predicted class
        ev = explainer.expected_value
        ev_array = np.array(ev)
        if ev_array.ndim == 1 and len(ev_array) > class_idx:
            base_value = float(ev_array[class_idx])
        elif ev_array.ndim == 0:
            base_value = float(ev_array)
        else:
            base_value = 0.0

        raw_features = []
        for i, feat in enumerate(features):
            raw_features.append({
                "name": feat,
                "display_name": FEATURE_DISPLAY_NAMES.get(feat, feat.replace("_", " ").title()),
                "value": vector[i],
                "shap_value": float(sv[i]),
            })

        return _format_explanation({
            "predicted_disease": predicted_disease,
            "features": raw_features,
            "base_value": base_value,
        })

    except Exception:
        logger.exception("Local SHAP computation failed")
        return _unavailable()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _format_explanation(data: dict) -> dict:
    """Normalise the raw API/local output into a consistent template-ready dict."""
    features_raw = data.get("features", [])

    # Keep only features with a non-zero SHAP contribution
    relevant = [f for f in features_raw if abs(f.get("shap_value", 0)) > 0.001]

    # Sort by absolute SHAP value descending; take top 10
    relevant.sort(key=lambda f: abs(f["shap_value"]), reverse=True)
    top_features = relevant[:10]

    # Normalise bars relative to the max magnitude (for percentage widths)
    max_abs = max((abs(f["shap_value"]) for f in top_features), default=1.0) or 1.0

    formatted = []
    for feat in top_features:
        sv = feat["shap_value"]
        direction = "positive" if sv >= 0 else "negative"
        bar_pct = round(abs(sv) / max_abs * 100, 1)
        formatted.append({
            "name": feat.get("name", ""),
            "display_name": feat.get("display_name",
                                     feat.get("name", "").replace("_", " ").title()),
            "value": feat.get("value", 0),           # 1 = symptom present
            "shap_value": round(sv, 4),
            "direction": direction,                   # "positive" | "negative"
            "bar_pct": bar_pct,                      # 0-100, used for CSS width
            "present": feat.get("value", 0) == 1,    # convenience flag
        })

    return {
        "predicted_disease": data.get("predicted_disease", "Unknown"),
        "features": formatted,
        "base_value": round(data.get("base_value", 0.0), 4),
        "available": True,
    }


def _unavailable() -> dict:
    return {"available": False, "features": [], "predicted_disease": "", "base_value": 0.0}
