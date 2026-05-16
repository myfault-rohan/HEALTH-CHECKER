import logging
import os
import requests

logger = logging.getLogger(__name__)

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8000")

def extract_symptoms_from_text(text):
    if not isinstance(text, str) or not text.strip():
        return []
    
    try:
        response = requests.post(
            f"{ML_SERVICE_URL}/extract_symptoms", 
            json={"text": text.strip()}, 
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("symptoms", [])
    except Exception:
        logger.exception("ML Service symptom extraction failed")
        
    return []
