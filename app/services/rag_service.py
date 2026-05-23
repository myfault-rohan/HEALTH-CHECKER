import logging
import os

from dotenv import load_dotenv
from google import genai

from app.services.disease_kb import _DESCRIPTIONS, _PRECAUTIONS, AYURVEDIC_REMEDIES

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize the Gemini API using the new google-genai SDK
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
    logger.info("Gemini API connected for Medical Chatbot (google-genai SDK)")
else:
    client = None
    logger.warning("GEMINI_API_KEY not found in environment. Chatbot will be disabled.")

# Build the Full Knowledge Base text once at startup
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

SYSTEM_PROMPT = (
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


def ask_medical_bot(query: str) -> str:
    """Process a user query using the full enterprise medical dataset context."""
    if not client:
        return "I'm sorry, my AI cognitive engine is currently offline. Please check the API key configuration."

    prompt = f"{SYSTEM_PROMPT}\n\n[Medical Database]\n{FULL_MEDICAL_CONTEXT}\n\nUser Query: {query}\n\nResponse:"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"LLM Generation failed: {e}")
        return "I apologize, but I am having trouble processing that right now. Please try again later."
