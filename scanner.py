import requests
import socket
import validators
from urllib.parse import urlparse
from datetime import datetime
import json
import os

from google.cloud import storage, pubsub_v1

# Constants (use these names in GCP)
BUCKET_NAME = "security-audit-portal"
TOPIC_NAME = "security-audit-portal"
PROJECT_ID = os.environ.get("GCP_PROJECT", "security-audit-portal")  # Replace in GCP UI

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

def upload_report_to_gcs(data, url):
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
    parsed = urlparse(url)
    filename = f"scan_reports/{timestamp}_{parsed.netloc}.json"
    
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
    return filename

def publish_to_pubsub(message_dict):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
    publisher.publish(topic_path, json.dumps(message_dict).encode("utf-8"))

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

        results = {
            "url": url,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "https_check": check_https(url),
            "secure_headers": check_headers(url),
            "open_ports": check_open_ports(domain),
            "cloud_storage_exposure": detect_cloud_storage(url)
        }

        # Upload to GCS
        path = upload_report_to_gcs(results, url)
        results["report_path"] = f"gs://{BUCKET_NAME}/{path}"

        # Publish to Pub/Sub
        publish_to_pubsub(results)

        return results
    except Exception as e:
        return {"error": f"Audit failed: {str(e)}"}
