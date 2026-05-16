import logging
import pickle
import os
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

try:
    import shap as shap_lib
    SHAP_AVAILABLE = True
except ImportError:
    shap_lib = None
    SHAP_AVAILABLE = False

app = FastAPI(title="Health Checker ML API", version="2.0")
logger = logging.getLogger(__name__)

CHATBOT_MODEL_PATH = "model/chatbot_model.pkl"
DISEASE_MODEL_PATH = "model/model.pkl"

chatbot_pipeline = None
disease_model = None
shap_explainer = None

try:
    with open(CHATBOT_MODEL_PATH, "rb") as f:
        chatbot_pipeline = pickle.load(f)
    with open(DISEASE_MODEL_PATH, "rb") as f:
        disease_model = pickle.load(f)
    if SHAP_AVAILABLE and disease_model is not None:
        shap_explainer = shap_lib.TreeExplainer(disease_model)
        logger.info("SHAP TreeExplainer initialised")
except Exception:
    logger.exception("Failed to load ML models")

class TextRequest(BaseModel):
    text: str

class SymptomsRequest(BaseModel):
    symptoms: List[int]

class ExplainRequest(BaseModel):
    """Accept symptoms as string names (human-readable) for the /explain endpoint."""
    symptoms: List[str]

FEATURES = [
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

@app.get("/health")
def health_check():
    return {"status": "healthy", "chatbot_loaded": chatbot_pipeline is not None, "disease_model_loaded": disease_model is not None}

@app.post("/extract_symptoms")
def extract_symptoms(req: TextRequest):
    if not chatbot_pipeline:
        raise HTTPException(status_code=500, detail="Chatbot model not loaded")
    pred = chatbot_pipeline.predict([req.text.lower()])[0]
    extracted = [FEATURES[i].replace("_", " ") for i, val in enumerate(pred) if val == 1]
    return {"symptoms": extracted}

@app.post("/predict_disease")
def predict_disease(req: SymptomsRequest):
    if not disease_model:
        raise HTTPException(status_code=500, detail="Disease prediction model not loaded")
    if len(req.symptoms) != len(FEATURES):
        raise HTTPException(status_code=422, detail=f"Expected {len(FEATURES)} symptoms, got {len(req.symptoms)}")
    input_df = pd.DataFrame([req.symptoms], columns=FEATURES)
    prediction = str(disease_model.predict(input_df)[0])
    return {"disease": prediction.replace("_", " ")}


@app.post("/explain")
def explain_prediction(req: ExplainRequest):
    """Return SHAP feature-importance values for a symptom set.

    Accepts symptom names (e.g. ['fever', 'cough']) and returns
    per-feature SHAP values for the top predicted disease class.
    """
    if not disease_model:
        raise HTTPException(status_code=500, detail="Disease prediction model not loaded")
    if not SHAP_AVAILABLE or shap_explainer is None:
        raise HTTPException(status_code=503, detail="SHAP not available on this service")

    # Normalise symptom names → feature keys
    selected = {s.strip().lower().replace(" ", "_") for s in req.symptoms}
    vector = [1 if f in selected else 0 for f in FEATURES]
    input_df = pd.DataFrame([vector], columns=FEATURES)

    # Predict
    predicted_class = disease_model.predict(input_df)[0]
    predicted_disease = str(predicted_class).replace("_", " ")

    # Compute SHAP values
    shap_values = shap_explainer.shap_values(input_df)

    # Multi-class: pick the slice for the predicted class
    if isinstance(shap_values, list):
        classes = disease_model.classes_.tolist()
        try:
            class_idx = classes.index(predicted_class)
        except ValueError:
            class_idx = 0
        sv = shap_values[class_idx][0]
    else:
        sv = shap_values[0]

    base_value = float(
        shap_explainer.expected_value[class_idx]
        if isinstance(shap_explainer.expected_value, (list, np.ndarray))
        else shap_explainer.expected_value
    )

    features_out = [
        {
            "name": feat,
            "display_name": feat.replace("_", " ").title(),
            "value": vector[i],
            "shap_value": float(sv[i]),
        }
        for i, feat in enumerate(FEATURES)
    ]

    return {
        "predicted_disease": predicted_disease,
        "base_value": base_value,
        "features": features_out,
    }
