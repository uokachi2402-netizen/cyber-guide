from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

genai.configure(api_key=os.environ.get("API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

@app.route("/")
def home():
    return "Server đang chạy!"

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")

    try:
        response = model.generate_content(question)
        return jsonify({"answer": response.text})
    except:
        return jsonify({"answer": "Lỗi AI!"})