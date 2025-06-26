from flask import Flask, request, jsonify, render_template
from scanner import perform_full_audit
import traceback
import os

# Point Flask to the 'templates' directory
app = Flask(__name__, template_folder="templates")

# Home route to render index.html
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# API endpoint to initiate a scan
@app.route("/scan", methods=["POST"])
def scan():
    try:
         # Validate that request contains JSON
        if not request.is_json:    
            return jsonify({"error": "Request must contain JSON data"}), 400
 
        data = request.get_json()
        url = data.get("url", "").strip()    # Extract URL from JSON payload
        if not url:
            return jsonify({"error": "Missing URL parameter"}), 400
        
        # Perform the security audit
        results = perform_full_audit(url)
        return jsonify(results)


    # Log and return server-side error details
    except Exception as e:
        app.logger.error(f"Scan error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Custom 404 error response
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

# Custom 500 error response
@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # Required for Cloud Run
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
