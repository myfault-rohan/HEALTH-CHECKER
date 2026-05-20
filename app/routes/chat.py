from flask import Blueprint, render_template, request, jsonify
from app.services.rag_service import ask_medical_bot

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

@chat_bp.route("/")
def index():
    return render_template("chat.html")

@chat_bp.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "No query provided"}), 400
        
    user_query = data["query"]
    
    # Generate RAG response
    response_text = ask_medical_bot(user_query)
    
    return jsonify({"response": response_text})
