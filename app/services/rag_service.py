import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

from app.services.disease_kb import _DESCRIPTIONS, AYURVEDIC_REMEDIES, _PRECAUTIONS

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize the Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    logger.info("Gemini API connected for Medical Chatbot")
else:
    model = None
    logger.warning("GEMINI_API_KEY not found in environment. Chatbot will be disabled.")

# Build the Full Knowledge Base text once
kb_parts = []
for disease, description in _DESCRIPTIONS.items():
    remedies = AYURVEDIC_REMEDIES.get(disease, [])
    precautions = _PRECAUTIONS.get(disease, [])
    
    kb_parts.append(
        f"--- {disease} ---\n"
        f"Description: {description}\n"
        f"Ayurvedic/Natural Remedies: {', '.join(remedies)}\n"
        f"Lifestyle Precautions: {', '.join(precautions)}\n"
    )

FULL_MEDICAL_CONTEXT = "\n".join(kb_parts)

def ask_medical_bot(query: str) -> str:
    """Process a user query using the full enterprise medical dataset context."""
    if not model:
        return "I'm sorry, my AI cognitive engine is currently offline. Please check the API key configuration."
        
    system_prompt = (
        "You are 'Health Checker AI', a professional, highly empathetic, and knowledgeable medical assistant. "
        "You have access to a proprietary clinical database of 41 conditions. "
        "CRITICAL RULES: "
        "1. USE ONLY THE PROVIDED MEDICAL CONTEXT to formulate your answer. "
        "2. Even if the user misspells symptoms (e.g. 'headace', 'stumach'), intelligently match them to the relevant conditions in your database. "
        "3. DO NOT prescribe synthetic or chemical medications. Always emphasize the Ayurvedic and natural remedies provided in the context. "
        "4. Always include a brief, compassionate disclaimer at the end stating that you are an AI assistant and they should consult a real healthcare provider for emergencies. "
        "5. Format your output cleanly with markdown (e.g., bullet points, bold text for emphasis). "
        "6. Do not mention that you were provided a text 'context' or 'database' in your response. Just answer naturally."
    )
    
    prompt = f"{system_prompt}\n\n[Medical Database]\n{FULL_MEDICAL_CONTEXT}\n\nUser Query: {query}\n\nResponse:"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"LLM Generation failed: {e}")
        return "I apologize, but I am having trouble processing that right now. Please try again later."
