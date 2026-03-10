"""Machine Learning disease prediction.

Single source of truth for ML inference. Do not reintroduce duplicate
predictor modules under ``app/services``.
"""

import pickle
from pathlib import Path
from typing import Iterable

# Fixed symptom order as trained in the model dataset.
FEATURE_SYMPTOMS = [
    "fever",
    "cough",
    "fatigue",
    "headache",
    "nausea",
    "vomiting",
    "chest_pain",
    "dizziness",
    "sore_throat",
    "runny_nose",
    "abdominal_pain",
    "diarrhea",
    "rash",
    "joint_pain",
    "chills",
    "sweating",
    "weight_loss",
    "anxiety",
    "depression",
    "blurred_vision",
    "shortness_of_breath",
    "muscle_pain",
    "weakness",
    "insomnia",
    "loss_of_appetite",
]

MODEL_PATH = Path(__file__).resolve().parent / "model" / "model.pkl"
if not MODEL_PATH.exists():
    MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"

MODEL = None
try:
    with MODEL_PATH.open("rb") as f:
        MODEL = pickle.load(f)
except Exception as e:
    print(f"Warning: Failed to load model from {MODEL_PATH}: {e}")

def _normalize_symptom_name(value):
    return str(value or "").strip().lower().replace("_", " ")

def predict_disease(symptoms):
    """
    Predict a disease using the trained Random Forest model.
    """
    if not isinstance(symptoms, (list, tuple)):
        raise ValueError("symptoms must be provided as a list or tuple.")

    if not symptoms:
        return "No clear match"

    if MODEL is None:
        return "No clear match (Model not loaded)"

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
        import pandas as pd
        input_df = pd.DataFrame([binary_vector], columns=FEATURE_SYMPTOMS)
        prediction = MODEL.predict(input_df)[0]
        # format prediction from Common_Cold to Common Cold
        return prediction.replace("_", " ")
    except Exception as e:
        print(f"Error during prediction: {e}")
        return "Prediction Error"
