from flask import Flask, request, jsonify, render_template
from scanner import perform_full_audit
import traceback

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({"error": "Request must contain JSON data"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        url = data.get("url")
        if not url:
            return jsonify({"error": "Missing URL parameter"}), 400

        # Strip whitespace from URL
        url = url.strip()
        
        # Perform the audit
        results = perform_full_audit(url)
        
        # Ensure the response is always JSON
        return jsonify(results)
        
    except Exception as e:
        # Log the full error for debugging
        app.logger.error(f"Scan endpoint error: {str(e)}")
        app.logger.error(traceback.format_exc())
        
        # Return JSON error response
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True ,host="0.0.0.0", port=8080)