from flask import Flask, request, jsonify, render_template
from scanner import perform_full_audit
import traceback
import os

app = Flask(__name__)

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

        results = perform_full_audit(url)
        return jsonify(results)

    except Exception as e:
        app.logger.error(f"Scan error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # default to 8080
    app.run(host="0.0.0.0", port=port)