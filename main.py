import http.client
import json
import time
from datetime import datetime, timedelta
import urllib.parse

# ===== CONFIGURATION =====
DOMAIN = "your_domain.api.cynet.com"
USERNAME = "your_username"
PASSWORD = "your_password"
CLIENT_ID = "your_client_id"

TOKEN_ENDPOINT = "/api/account/token"
ALERTS_ENDPOINT = "/api/alerts"

POLL_INTERVAL = 60  # seconds
TOKEN_BUFFER = 55 * 60  # Refresh token after 55 minutes


class CynetClient:
    def __init__(self):
        self.access_token = None
        self.token_expiry = 0
        # Initialize to 24 hours ago for the first run
        self.last_seen = datetime.utcnow() - timedelta(hours=24)

    def authenticate(self):
        conn = http.client.HTTPSConnection(DOMAIN)
        payload = json.dumps({"user_name": USERNAME, "password": PASSWORD})
        headers = {'Content-Type': "application/json", 'Accept': "application/json"}

        conn.request("POST", TOKEN_ENDPOINT, payload, headers)
        res = conn.getresponse()

        if res.status != 200:
            raise Exception(f"Authentication failed: {res.read().decode()}")

        data = json.loads(res.read().decode("utf-8"))
        self.access_token = data.get("access_token")
        self.token_expiry = time.time() + TOKEN_BUFFER
        print("[+] Token acquired successfully")

    def ensure_token(self):
        if not self.access_token or time.time() >= self.token_expiry:
            print("[*] Refreshing token...")
            self.authenticate()

    def get_alerts(self):
        self.ensure_token()
        conn = http.client.HTTPSConnection(DOMAIN)
        
        # Format: YYYY-MM-DD hh:mm:ss
        formatted_last_seen = self.last_seen.strftime("%Y-%m-%d %H:%M:%S")
        params = urllib.parse.urlencode({"LastSeen": formatted_last_seen})
        endpoint = f"{ALERTS_ENDPOINT}?{params}"

        headers = {
            'client_id': CLIENT_ID,
            'access_token': self.access_token,
            'Accept': "application/json"
        }

        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()

        if res.status == 401:
            print("[!] Token expired. Re-authenticating...")
            self.authenticate()
            return self.get_alerts()

        if res.status != 200:
            raise Exception(f"Failed to fetch alerts: {res.read().decode()}")

        data = json.loads(res.read().decode("utf-8"))
        self.last_seen = datetime.utcnow() # Advance the cursor
        return data


if __name__ == "__main__":
    client = CynetClient()
    print("[*] Starting Cynet Alert Collector...")
    
    while True:
        try:
            alerts = client.get_alerts()
            if alerts:
                print(f"[+] Found {len(alerts)} New Alerts")
                # Send to SIEM or process here
                print(json.dumps(alerts, indent=2))
            else:
                print("[-] No new alerts since last check")
        except Exception as e:
            print(f"[ERROR] {e}")
        
        time.sleep(POLL_INTERVAL)
