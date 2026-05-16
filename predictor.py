"""Machine Learning disease prediction client.

Connects to the FastAPI ML Microservice to perform disease inference.
"""
import logging
import os
import requests

logger = logging.getLogger(__name__)

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8000")

# Fixed symptom order as trained in the model dataset.
FEATURE_SYMPTOMS = [
    "headache", "dizziness", "blurred_vision", "confusion", "cough", 
    "shortness_of_breath", "chest_pain", "wheezing", "palpitations", 
    "abdominal_pain", "nausea", "vomiting", "diarrhea", "constipation", 
    "bloating", "heartburn", "urinary_problems", "fever", "fatigue", 
    "chills", "night_sweats", "weight_loss", "insomnia", "loss_of_appetite", 
    "sore_throat", "runny_nose", "sneezing", "congestion", "rash", 
    "swelling", "joint_pain", "back_pain", "muscle_pain", "stiffness", 
    "acidity", "leg_pain", "body_weakness", "stomach_pain", "waist_pain", 
    "watery_eyes", "nightfall", "menstrual_pain", "dehydration", "cold", "stress"
]

def _normalize_symptom_name(value):
    return str(value or "").strip().lower().replace("_", " ")

def predict_disease(symptoms):
    """
    Predict a disease using the FastAPI Machine Learning Microservice.
    """
    if not isinstance(symptoms, (list, tuple)):
        raise ValueError("symptoms must be provided as a list or tuple.")

    if not symptoms:
        return "No clear match"

    selected = {
        _normalize_symptom_name(value)
        for value in symptoms
        if _normalize_symptom_name(value)
    }

    # Convert to binary vector
    binary_vector = []
    for symptom in FEATURE_SYMPTOMS:
        if symptom.replace("_", " ") in selected:
            binary_vector.append(1)
        else:
            binary_vector.append(0)

    try:
        response = requests.post(
            f"{ML_SERVICE_URL}/predict_disease", 
            json={"symptoms": binary_vector}, 
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("disease", "Prediction Error")
        logger.warning("ML Service returned status %s", response.status_code)
    except Exception:
        logger.exception("ML Service prediction request failed")
    return "Prediction Error"
