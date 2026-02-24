from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Allow frontend to call the API

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "Empty query"}), 400

        WEBHOOK = "https://n8n.n8nautomations.me/webhook/51b66e9e-15d3-4418-a304-030d357e35a2"

        resp = requests.post(
            WEBHOOK,
            json={"chatInput": query},  # IMPORTANT match your n8n input
            timeout=30
        )

        print("Webhook status:", resp.status_code)
        print("Webhook response:", resp.text)

        try:
            result = resp.json()
            answer = result if isinstance(result, str) else result.get("output", result)
        except:
            answer = resp.text

        return jsonify({"answer": answer})

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
