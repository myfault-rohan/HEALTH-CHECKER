"""Chat blueprint — AI Medical Assistant routes."""
import logging

from flask import Blueprint, jsonify, render_template, request, session

from app.routes.helpers import login_required
from app.services.audit_service import AuditAction, log_event
from app.services.rag_service import ask_medical_bot

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("", strict_slashes=False)
@login_required
def index():
    """Render the AI Medical Assistant chat page."""
    return render_template("chat.html")


@chat_bp.route("/ask", methods=["POST"])
@login_required
def ask():
    """Handle a medical query and return an AI-generated response."""
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "No query provided"}), 400

    user_query = data["query"]
    email = session.get("email", "anonymous")
    log_event(email, AuditAction.CHAT_QUERY, resource=user_query[:80])

    response_text = ask_medical_bot(user_query)
    return jsonify({"response": response_text})
