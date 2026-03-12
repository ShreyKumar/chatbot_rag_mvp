# app.py
import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template
from bedrock_kb_rag import retrieve_and_generate, health_probe

app = Flask(__name__)

KB_TOP_K = int(os.getenv("KB_TOP_K", "5"))


@app.route("/")
def index():
    return render_template("index.html")


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


@app.route("/health", methods=["GET"])
def health():
    """
    Call this right after you paste new SSO temp creds into .env.
    If creds are expired/invalid, this will return ok:false with the AWS error.
    """
    return jsonify(health_probe())
    

if __name__ == "__main__":
    print("hello")
    app.run(debug=True)
    