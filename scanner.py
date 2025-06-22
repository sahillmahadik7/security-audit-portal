import base64
import json
import requests
import socket
import validators
from urllib.parse import urlparse
from google.cloud import storage
from datetime import datetime


# --- Audit Functions ---
def check_https(url):
    return url.startswith("https://")


def check_headers(url):
    required_headers = ['Content-Security-Policy', 'X-Frame-Options']
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        headers = response.headers
        return {h: headers.get(h, 'Missing') for h in required_headers}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout - server took too long to respond"}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection error - unable to reach the server"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def check_open_ports(domain, ports=[80, 443, 21, 22]):
    open_ports = []
    for port in ports:
        try:
            with socket.create_connection((domain, port), timeout=3):
                open_ports.append(port)
        except:
            pass
    return open_ports


def detect_cloud_storage(url):
    indicators = ["s3.amazonaws.com", "storage.googleapis.com", "blob.core.windows.net"]
    return any(indicator in url for indicator in indicators)


def perform_full_audit(url):
    if not url:
        return {"error": "URL is required"}

    if not validators.url(url):
        return {"error": "Invalid URL format"}

    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        if not domain:
            return {"error": "Could not extract domain from URL"}

        return {
            "url": url,
            "scanned_at": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            "https_check": check_https(url),
            "secure_headers": check_headers(url),
            "open_ports": check_open_ports(domain),
            "cloud_storage_exposure": detect_cloud_storage(url)
        }
    except Exception as e:
        return {"error": f"Audit failed: {str(e)}"}


# --- Cloud Function entry point ---
def pubsub_entry(event, context):
    try:
        message = base64.b64decode(event['data']).decode('utf-8')
        data = json.loads(message)
        url = data.get('url')

        if not url:
            print("No URL provided in message")
            return

        audit_result = perform_full_audit(url)

        # Save to Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket("security-audit-portal")  # 🔁 Replace with your bucket name

        domain_clean = urlparse(url).netloc.replace('.', '_').replace(':', '_')
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')
        filename = f"results/{timestamp}__{domain_clean}.json"

        blob = bucket.blob(filename)
        blob.upload_from_string(json.dumps(audit_result, indent=2), content_type='application/json')

        print(f"Audit complete and saved to {filename}")

    except Exception as e:
        print(f"Function failed: {str(e)}")
