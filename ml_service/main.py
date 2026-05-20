"""
Health Checker ML Microservice
================================
FastAPI service exposing versioned REST endpoints for disease prediction,
SHAP explainability, NLP symptom extraction, and a real-time WebSocket
vitals stream.

Interactive docs: http://localhost:8000/docs
"""
import asyncio
import logging
import pickle
import random
from typing import List

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

# ── SHAP (optional) ──────────────────────────────────────────────────────────
try:
    import shap as shap_lib
    SHAP_AVAILABLE = True
except ImportError:
    shap_lib = None
    SHAP_AVAILABLE = False

# ── App definition ────────────────────────────────────────────────────────────
app = FastAPI(
    title="Health Checker ML API",
    description=(
        "Production ML microservice for disease prediction, explainable AI (SHAP), "
        "NLP symptom extraction, and real-time wearable vitals streaming. "
        "Built with HistGradientBoostingClassifier trained on 57,000+ symptom-disease records."
    ),
    version="2.0.0",
    contact={"name": "Health Checker Pro", "url": "https://github.com/myfault-rohan/HEALTH-CHECKER"},
    license_info={"name": "MIT"},
)
logger = logging.getLogger(__name__)

# ── Versioned router ──────────────────────────────────────────────────────────
v1 = APIRouter(prefix="/v1", tags=["v1"])

# ── Model loading ─────────────────────────────────────────────────────────────
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

# ── Feature definition ────────────────────────────────────────────────────────
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

# ── Request / Response schemas ────────────────────────────────────────────────
class TextRequest(BaseModel):
    text: str = Field(..., example="I have a headache and fever with body ache")

class SymptomsRequest(BaseModel):
    symptoms: List[int] = Field(
        ...,
        description=f"Binary vector of {len(FEATURES)} symptom flags (0 or 1), in canonical order.",
        example=[0]*len(FEATURES)
    )

class ExplainRequest(BaseModel):
    symptoms: List[str] = Field(
        ...,
        description="List of symptom names as strings (e.g. ['fever', 'cough']).",
        example=["fever", "cough", "fatigue"]
    )

class HealthResponse(BaseModel):
    status: str
    version: str
    disease_model_loaded: bool
    chatbot_loaded: bool
    shap_available: bool

# ── Utility endpoints (unversioned) ──────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Kubernetes-compatible liveness probe. Returns service status and model load state."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "disease_model_loaded": disease_model is not None,
        "chatbot_loaded": chatbot_pipeline is not None,
        "shap_available": SHAP_AVAILABLE and shap_explainer is not None,
    }

@app.websocket("/ws/vitals")
async def websocket_vitals(websocket: WebSocket):
    """
    Real-time wearable vitals stream over WebSocket.

    Streams JSON every second with keys: `bpm`, `spo2`, `temp`.
    Occasionally injects anomaly spikes (bpm >100, spo2 <95) for demonstration.
    """
    await websocket.accept()
    try:
        while True:
            vitals = {
                "bpm": random.randint(65, 95),
                "spo2": random.randint(96, 100),
                "temp": round(random.uniform(36.4, 37.2), 1)
            }
            if random.random() > 0.95:
                vitals["bpm"] = random.randint(110, 130)
                vitals["spo2"] = random.randint(90, 93)
            await websocket.send_json(vitals)
            await asyncio.sleep(1)
    except Exception:
        logger.info("WebSocket client disconnected")

# ── v1 endpoints ──────────────────────────────────────────────────────────────
@v1.post(
    "/extract_symptoms",
    summary="Extract symptoms from free text",
    response_description="List of recognized symptom strings",
    tags=["NLP"],
)
def extract_symptoms(req: TextRequest):
    """
    Run the TF-IDF multi-label NLP pipeline to extract structured symptom flags
    from a free-text patient description.

    Returns a list of canonical symptom names found in the input.
    """
    if not chatbot_pipeline:
        raise HTTPException(status_code=500, detail="NLP model not loaded")
    pred = chatbot_pipeline.predict([req.text.lower()])[0]
    extracted = [FEATURES[i].replace("_", " ") for i, val in enumerate(pred) if val == 1]
    return {"symptoms": extracted, "count": len(extracted)}


@v1.post(
    "/predict_disease",
    summary="Predict disease from binary symptom vector",
    response_description="Predicted disease name",
    tags=["Prediction"],
)
def predict_disease(req: SymptomsRequest):
    """
    Run the HistGradientBoostingClassifier on a binary symptom vector.

    Input must be a list of exactly 45 integers (0 or 1), one per canonical symptom feature.
    Returns the top predicted disease name.
    """
    if not disease_model:
        raise HTTPException(status_code=500, detail="Disease model not loaded")
    if len(req.symptoms) != len(FEATURES):
        raise HTTPException(
            status_code=422,
            detail=f"Expected {len(FEATURES)} symptom flags, got {len(req.symptoms)}"
        )
    input_df = pd.DataFrame([req.symptoms], columns=FEATURES)
    prediction = str(disease_model.predict(input_df)[0])
    return {"disease": prediction.replace("_", " ")}


@v1.post(
    "/explain",
    summary="SHAP explanation for a symptom set",
    response_description="Per-feature SHAP values for the predicted disease class",
    tags=["Explainability (XAI)"],
)
def explain_prediction(req: ExplainRequest):
    """
    Compute **SHAP (SHapley Additive exPlanations)** values for a given symptom list.

    Returns per-feature SHAP impact scores showing which symptoms drove the prediction
    and in which direction (positive = supports diagnosis, negative = contradicts).

    This endpoint powers the waterfall chart on the Conditions page.
    """
    if not disease_model:
        raise HTTPException(status_code=500, detail="Disease model not loaded")
    if not SHAP_AVAILABLE or shap_explainer is None:
        raise HTTPException(status_code=503, detail="SHAP not available")

    selected = {s.strip().lower().replace(" ", "_") for s in req.symptoms}
    vector = [1 if f in selected else 0 for f in FEATURES]
    input_df = pd.DataFrame([vector], columns=FEATURES)

    predicted_class = disease_model.predict(input_df)[0]
    predicted_disease = str(predicted_class).replace("_", " ")

    shap_values = shap_explainer.shap_values(input_df)

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
            "shap_value": round(float(sv[i]), 4),
        }
        for i, feat in enumerate(FEATURES)
    ]

    return {
        "predicted_disease": predicted_disease,
        "base_value": base_value,
        "features": features_out,
        "method": "SHAP TreeExplainer",
    }


# ── Mount versioned router ────────────────────────────────────────────────────
app.include_router(v1)
