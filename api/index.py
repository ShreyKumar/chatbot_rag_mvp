import os
import sys

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from flask import Flask, request, jsonify, send_from_directory
from bedrock_kb_rag import retrieve_and_generate, health_probe

app = Flask(__name__, static_folder='../static', template_folder='../templates')

KB_TOP_K = int(os.getenv("KB_TOP_K", "5"))


@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_msg = (data.get("message") or "").strip()

    if not user_msg:
        return jsonify({"error": "message is required"}), 400

    try:
        answer = retrieve_and_generate(user_msg, top_k=KB_TOP_K)
    except Exception as e:
        return jsonify({"error": "RAG call failed", "details": str(e)}), 500

    return jsonify({"answer": answer})


@app.route("/api/health", methods=["GET"])
def health():
    """
    Call this to validate AWS credentials and Bedrock connection.
    """
    return jsonify(health_probe())


# Vercel expects the Flask app to be named 'app'