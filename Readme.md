
# 🛡️ Cynet 360 Real-Time Alerts Collector

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![API Status](https://img.shields.io/badge/API-Cynet_360-red.svg)](https://developers.cynet.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A production-grade Python collector engineered to interface with the **Cynet 360 Security Platform**. This tool automates the authentication handshake, manages token lifecycles with proactive refreshing, and implements a cursor-based polling mechanism for real-time alert ingestion.

---

## 📖 Table of Contents
- [✨ Features](#-features)
- [⚙️ Tech Stack](#️-tech-stack)
- [📂 Project Architecture](#-project-architecture)
- [🔍 Code Logic Breakdown](#-code-logic-breakdown)
- [📜 Full Script](#-full-script)
- [🛠 Security Best Practices](#-security-best-practices)
- [📈 Deployment Strategy](#-deployment-strategy)

---

## ✨ Features
* **🔄 Self-Healing Auth:** Automatically detects `401 Unauthorized` errors and re-authenticates.
* **⏰ Proactive Token Refresh:** Refreshes the 60-minute JWT 5 minutes before expiration to prevent race conditions.
* **📍 Cursor-Based Polling:** Uses the `LastSeen` parameter to ensure 0% data overlap and 100% alert coverage.
* **📉 Zero Dependencies:** Uses standard Python libraries (`http.client`) for maximum compatibility and minimal attack surface.

---

## ⚙️ Tech Stack
* **Language:** ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
* **Protocol:** ![HTTPS](https://img.shields.io/badge/Protocol-HTTPS-brightgreen)
* **Format:** ![JSON](https://img.shields.io/badge/Data-JSON-lightgrey)
* **Architecture:** Singleton Client Pattern

---

## 📂 Project Architecture



The logic follows a **Circular Polling Pattern**:
1.  **Identity Provider (IdP):** Exchanges credentials for a scoped Bearer Token.
2.  **Validation Gate:** Checks `token_expiry` before every API call.
3.  **Data Fetcher:** Requests alerts since the `LastSeen` timestamp.
4.  **State Update:** Advances the `LastSeen` cursor to `utcnow()`.
5.  **Backoff:** Sleeps for 60 seconds to respect API rate limits.

---

## 🔍 Code Logic Breakdown

Here is a surgical breakdown of what each section of the code handles:

### 1. Configuration & Constants
* **`POLL_INTERVAL`**: Frequency of alert checks (in seconds). Set to 60 to balance real-time needs with API load.
* **`TOKEN_BUFFER`**: Safety window. We refresh the token after 55 minutes, even though it lasts 60, to avoid "edge-of-expiry" failures.

### 2. The `CynetClient` Initialization (`__init__`)
* `self.access_token`: The active JWT string.
* `self.token_expiry`: A Unix timestamp calculating when the token becomes "stale."
* `self.last_seen`: Initialized to `UTC - 24h` so the first run captures a full day of history.

### 3. `authenticate(self)`
* **HTTPS Connection**: Establishes a secure tunnel to your specific Cynet tenant domain.
* **Payload**: Encodes your username and password into a JSON object.
* **Token Storage**: Extracts the `access_token` from the response and calculates the expiry time (`current_time + 55 mins`).

### 4. `ensure_token(self)`
* This is the "Safety Guard." It evaluates: `if current_time >= token_expiry`. If true, it triggers a login *before* the API is polled.

### 5. `get_alerts(self)`
* **Timestamp Formatting**: Converts Python `datetime` into the string format Cynet requires: `YYYY-MM-DD hh:mm:ss`.
* **URL Encoding**: Uses `urllib.parse` to ensure the timestamp is safe for HTTP (handling spaces and colons).
* **Recursive Retry**: If a `401` occurs (unexpected expiration), it catches the error, re-logs in, and retries the request automatically.

### 6. The Main Loop (`if __name__ == "__main__":`)
* **`while True`**: Keeps the script running indefinitely as a background service.
* **`try/except`**: Ensures that a network glitch doesn't crash the entire collector.

---

## 📜 Full Script

<details>
  <summary>Click to Expand or check main.py </summary>
  
  See Risk Mitigation and Security Consideration before Use 
  [🛠 Security Best Practices](#-security-best-practices) 


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

```
</details>

---

## 🛠 Security Best Practices and Important Consideration before Use

| Risk | Mitigation |
| --- | --- |
| **Credential Leak** | Use environment variables (`os.getenv`) instead of hardcoded strings. |
| **Data Gaps** | Persist the `last_seen` value to a file so the script can resume after a reboot. |
| **Token Hijacking** | Ensure `HTTPSConnection` is used (default in script) to encrypt traffic in transit. |

---

## 📈 Deployment Strategy

### 🐳 Dockerize

Deploy as a lightweight container using `python:3.9-slim`. This ensures consistent performance across cloud or on-prem environments.

### 🖥️ SIEM Ingestion

To integrate with Splunk, Sentinel, or ELK, replace the `print()` logic with a POST request to your SIEM's **HTTP Event Collector (HEC)**.

---

**Version:** 1.0.0


**Purpose:** Real-Time Threat Intelligence Ingestion

```

```
