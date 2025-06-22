from flask import Flask, request, jsonify, render_template
from google.cloud import pubsub_v1
import traceback
import os
import json

app = Flask(__name__)

# Setup Pub/Sub
publisher = pubsub_v1.PublisherClient()
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
topic_path = publisher.topic_path(project_id, "security-audit-portal")

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must contain JSON data"}), 400

        data = request.get_json()
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "Missing URL parameter"}), 400

        # Publish to Pub/Sub
        payload = json.dumps({"url": url}).encode("utf-8")
        future = publisher.publish(topic_path, payload)
        future.result()  # Ensure publish completes

        return jsonify({"message": "Scan request submitted successfully"}), 200

    except Exception as e:
        app.logger.error(f"Scan endpoint error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True ,host="0.0.0.0", port=8080)
