"""
OZZRIK.CO — 1.62B Tokens of AI Masterclass
Secure Backend Server for Razorpay Orders API & Video Streaming
"""

import os
import sys
import json
import base64
import hmac
import hashlib
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("PORT", 3000))
KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_live_ToTcNOLxSRHZ7U")
KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "dJDLnFDhA4BXxsoJnEulOpD4")

# Read from .env if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == "RAZORPAY_KEY_ID":
                    KEY_ID = v
                elif k == "RAZORPAY_KEY_SECRET":
                    KEY_SECRET = v
                elif k == "PORT":
                    try:
                        PORT = int(v)
                    except:
                        pass

class RazorpayStoreHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS and Range headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/create-order":
            self.handle_create_order()
        elif self.path == "/api/verify-payment":
            self.handle_verify_payment()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_create_order(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
            data = json.loads(post_body) if post_body else {}

            amount = data.get("amount", 5900) # 5900 paise = 59 INR
            currency = data.get("currency", "INR")
            receipt = "rcpt_" + os.urandom(4).hex()

            payload = json.dumps({
                "amount": amount,
                "currency": currency,
                "receipt": receipt,
                "payment_capture": 1,
                "notes": {
                    "product": "1.62B Tokens of AI Masterclass",
                    "brand": "OZZRIK.CO"
                }
            }).encode("utf-8")

            req = urllib.request.Request("https://api.razorpay.com/v1/orders", data=payload)
            auth_str = f"{KEY_ID}:{KEY_SECRET}"
            b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            req.add_header("Authorization", f"Basic {b64_auth}")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req) as resp:
                resp_data = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp_data)

        except urllib.error.HTTPError as e:
            err_content = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err_content)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def handle_verify_payment(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(post_body)

            order_id = data.get("razorpay_order_id", "")
            payment_id = data.get("razorpay_payment_id", "")
            signature = data.get("razorpay_signature", "")

            # Verify signature: HMAC SHA256(order_id + "|" + payment_id, secret)
            generated_signature = hmac.new(
                KEY_SECRET.encode("utf-8"),
                f"{order_id}|{payment_id}".encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            if generated_signature == signature:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"verified": True, "status": "success"}).encode("utf-8"))
            else:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"verified": False, "error": "Signature mismatch"}).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

def run():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, RazorpayStoreHandler)
    print(f"=======================================================")
    print(f"  OZZRIK.CO — 1.62B Tokens of AI Masterclass Server")
    print(f"  Live on: http://localhost:{PORT}")
    print(f"  Razorpay Key ID: {KEY_ID}")
    print(f"=======================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    run()
