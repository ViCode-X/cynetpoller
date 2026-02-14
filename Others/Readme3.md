
# 🛡️ Cynet 360 Real-Time Alerts Collector

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Production--Ready-success?style=for-the-badge)](https://github.com/)
[![Security](https://img.shields.io/badge/Security-Handled-red?style=for-the-badge)](https://www.cynet.com/)

A production-grade Python collector designed to authenticate with the **Cynet API**, handle automatic token refreshing (60-minute TTL), and retrieve security alerts dynamically using the `LastSeen` cursor.

---

## 📌 Overview

This project implements a high-reliability polling client for Cynet 360 that:

* 🔑 **Authenticates** via the `/api/account/token` endpoint.
* ⏳ **Refreshes Tokens** automatically every 55 minutes to prevent session drops.
* 📡 **Fetches Alerts** using the `/api/alerts` GET method.
* 🕒 **Stateful Polling** via dynamic `LastSeen` updates.
* 🔁 **Infinite Loop** logic designed for near real-time SOC visibility.

---

## 🏗 Architecture Flow




graph TD
    A[Start Collector] --> B{Token Valid?}
    B -- No --> C[POST /api/account/token]
    C --> D[Store JWT & Expiry]
    B -- Yes --> E[GET /api/alerts?LastSeen=...]
    D --> E
    E --> F[Update LastSeen Cursor]
    F --> G[Sleep 60s]
    G --> B

---

## 🧰 Tech Stack

| Component | Purpose |
| --- | --- |
| 🐍 **Python 3** | Core runtime engine |
| 🌐 **http.client** | Native HTTPS communication (zero external dependencies) |
| 🧾 **JSON** | API payload serialization & deserialization |
| ⏰ **datetime** | Calculation of dynamic ISO-style timestamps |
| 🔁 **time** | Managing polling backoff and token TTL |

---

## 🔐 Authentication Model

The Cynet API requires two primary identifiers in the header of every request:

| Header | Description |
| --- | --- |
| `client_id` | Your specific tenant identifier. |
| `access_token` | The bearer token (Valid for 60 minutes). |

> **Note:** This collector implements a `TOKEN_BUFFER` of 55 minutes. This ensures that even if a request takes several seconds, the token will not expire mid-transaction.

---

## 🕒 LastSeen Format Requirement

The API expects a very specific string format for the cursor: `YYYY-MM-DD hh:mm:ss`.

* **Initialization:** The script looks back 24 hours on the first run.
* **Persistence:** It updates the cursor immediately after a successful response to prevent duplicate data ingestion.

---

## 📜 Full Production Script

```python
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
        print("[+] Token acquired")

    def ensure_token(self):
        if not self.access_token or time.time() >= self.token_expiry:
            print("[*] Refreshing token...")
            self.authenticate()

    def get_alerts(self):
        self.ensure_token()
        conn = http.client.HTTPSConnection(DOMAIN)
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
            print("[!] Token expired unexpectedly. Re-authenticating...")
            self.authenticate()
            return self.get_alerts()

        if res.status != 200:
            raise Exception(f"Failed to fetch alerts: {res.read().decode()}")

        data = json.loads(res.read().decode("utf-8"))
        self.last_seen = datetime.utcnow()
        return data

if __name__ == "__main__":
    client = CynetClient()
    while True:
        try:
            alerts = client.get_alerts()
            if alerts:
                print(f"[+] New Alerts: {len(alerts)}")
                print(json.dumps(alerts, indent=2))
            else:
                print("[-] No new alerts")
        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(POLL_INTERVAL)

```

---

## 🔎 Line-by-Line Explanation

### 📦 Imports

* `http.client`: 🌐 Standard library for making HTTPS requests without needing `requests` package.
* `json`: 🧾 Encodes credentials and decodes alert payloads.
* `time`: ⏳ Controls the `sleep` interval and Unix timestamp comparisons for the token.
* `datetime`: 🕒 Handles the conversion of time objects into the Cynet-required string format.
* `urllib.parse`: 🔗 Safely escapes spaces and colons in the URL query string.

### 🏗 CynetClient Class

* `__init__`: Sets the initial "lookback" to 24 hours ago.
* `authenticate()`: Performs the POST request. It stores the `access_token` and calculates `expiry = now + 55 mins`.
* `ensure_token()`: A validation wrapper. It checks the clock before every call to ensure the session hasn't timed out.
* `get_alerts()`:
* Constructs the dynamic URL with `LastSeen`.
* Sends the `client_id` (mandatory) and the `access_token`.
* **Self-Healing:** If a 401 (Unauthorized) is caught, it triggers `authenticate()` and retries the request once.



---

## 🛡 Security Best Practices

| Risk | Recommendation |
| --- | --- |
| 🔑 **Hardcoded Credentials** | Use `os.getenv('CYNET_PWD')` instead of plain text strings. |
| 💾 **State Loss** | Persist `last_seen` to a file (`state.txt`) so the script remembers its place after a reboot. |
| 🔁 **Duplicate Alerts** | Store a small cache of the last 10 `alert_id`s to deduplicate identical timestamps. |
| 🧾 **No Logging** | Replace `print()` with the `logging` module to output to `/var/log/cynet.log`. |

---

## 🚀 Deployment & SIEM Integration

### 🐳 Docker Deployment

Run this collector as a lightweight container to ensure 24/7 uptime.

```bash
docker build -t cynet-collector .
docker run -d --restart always --name cynet-alert-service cynet-collector

```

### 📡 SIEM Target Examples

* **Logstash:** Forward output to a TCP/UDP port.
* **Splunk HEC:** Use a `POST` request inside the main loop to send alerts directly to Splunk.
* **Sentinel:** Integrate via the Log Analytics Workspace API.

---

## 📌 Conclusion

This project provides a **secure, autonomous, and scalable** foundation for Cynet 360 alert ingestion. By handling the token lifecycle and cursor-based polling automatically, it is ready for deployment in modern SOC automation pipelines.

**Author:** Vicode-X

**Version:** 1.0.0

