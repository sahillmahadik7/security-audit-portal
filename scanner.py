#importing all dependencies
import requests
import socket
import validators
from urllib.parse import urlparse

#function for checking the http header is secure or not :
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


# Thic functions checks if there is any open port or not :
def check_open_ports(domain, ports=[80, 443, 21, 22]):
    open_ports = []
    for port in ports:
        try:
            with socket.create_connection((domain, port), timeout=3):  # this will create a connection between server and client on a single port at a time and see if it responds or not. If response came than that port is open else it is closed 
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
        # Parse domain from URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        if not domain:
            return {"error": "Could not extract domain from URL"}

        return {
            "https_check": check_https(url),
            "secure_headers": check_headers(url),
            "open_ports": check_open_ports(domain),
            "cloud_storage_exposure": detect_cloud_storage(url)
        }
    except Exception as e:
        return {"error": f"Audit failed: {str(e)}"}
