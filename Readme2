Below is a clean, professional, and well-structured **README.md** in full Markdown format for your project.

You can copy this directly into a `README.md` file in your repository.

---

# 🛡️ Cynet 360 Real-Time Alerts Collector

> 🔐 Production-ready Python collector that authenticates with the Cynet API, handles token expiration automatically, and retrieves alerts dynamically using the `LastSeen` parameter.

---

## 📌 Overview

This project implements a **real-time alert polling client** for Cynet 360 that:

* 🔑 Authenticates via `/api/account/token`
* ⏳ Automatically refreshes tokens (60-minute timeout handling)
* 📡 Fetches alerts using `/api/alerts`
* 🕒 Dynamically updates `LastSeen`
* 🔁 Continuously polls in near real-time
* 🛠 Designed for SIEM ingestion or SOC automation pipelines

---

# 🏗 Architecture Flow

```text
┌───────────────┐
│ Authenticate  │  → Receive access_token (60 min TTL)
└───────┬───────┘
        │
        ▼
┌────────────────────┐
│ Ensure Token Valid │
└───────┬────────────┘
        │
        ▼
┌──────────────────────────────┐
│ GET /api/alerts?LastSeen=... │
└───────┬──────────────────────┘
        │
        ▼
┌────────────────────┐
│ Update LastSeen    │
└───────┬────────────┘
        │
        ▼
     Sleep 60s
        │
        └── Repeat
```

---

# 🧰 Tech Stack

| Component        | Purpose                         |
| ---------------- | ------------------------------- |
| 🐍 Python 3      | Core scripting                  |
| 🌐 `http.client` | HTTPS communication             |
| 🧾 JSON          | API payload handling            |
| ⏰ `datetime`     | Dynamic time calculations       |
| 🔁 `time`        | Polling + token expiry handling |

---

# 🔐 Authentication Model

The Cynet API requires:

| Header         | Purpose                      |
| -------------- | ---------------------------- |
| `client_id`    | Tenant identification        |
| `access_token` | Bearer token (valid 60 mins) |

Token is obtained via:

```
POST /api/account/token
```

---

# 🕒 LastSeen Format Requirement

Cynet requires:

```
YYYY-MM-DD hh:mm:ss
```

Example:

```
2026-02-13 18:30:00
```

This script dynamically sets:

```
LastSeen = current_utc_time - 24 hours
```

Then updates it after every successful poll.

---

# 📜 Full Production Script

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

        payload = json.dumps({
            "user_name": USERNAME,
            "password": PASSWORD
        })

        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

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

        params = urllib.parse.urlencode({
            "LastSeen": formatted_last_seen
        })

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
                print("[+] New Alerts:")
                print(json.dumps(alerts, indent=2))
            else:
                print("[-] No new alerts")

        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(POLL_INTERVAL)
```

---

# 🔎 Line-by-Line Explanation

## 📦 Imports

```python
import http.client
```

🌐 Handles HTTPS API communication.

```python
import json
```

🧾 Serializes/deserializes JSON payloads.

```python
import time
```

⏳ Manages polling intervals & token expiry.

```python
from datetime import datetime, timedelta
```

🕒 Generates dynamic `LastSeen`.

```python
import urllib.parse
```

🔗 Encodes URL query parameters safely.

---

## ⚙ Configuration Section

Defines:

* Domain
* Credentials
* Endpoints
* Polling interval
* Token refresh buffer

`TOKEN_BUFFER = 55 * 60`
→ Refresh before full 60 min expiry for safety.

---

## 🏗 CynetClient Class

Encapsulates:

* Authentication logic
* Token validation
* Alert retrieval
* State tracking

---

### 🔐 `authenticate()`

* Opens HTTPS connection
* Sends credentials
* Receives `access_token`
* Sets expiry timestamp

---

### ⏳ `ensure_token()`

* Checks if token expired
* Refreshes if needed
* Prevents 401 failures

---

### 📡 `get_alerts()`

1. Validates token
2. Formats `LastSeen`
3. URL-encodes query
4. Sends GET request
5. Handles 401 auto-refresh
6. Updates `LastSeen`

---

## 🔁 Main Loop

```python
while True:
```

* Fetch alerts
* Print results
* Sleep 60 seconds
* Repeat indefinitely

---

# 🛡 Security Best Practices

| Risk                          | Recommendation                        |
| ----------------------------- | ------------------------------------- |
| 🔑 Hardcoded credentials      | Use environment variables             |
| 💾 Lost `LastSeen` on restart | Persist to file/DB                    |
| 🔁 Duplicate alerts           | Store last alert ID                   |
| 🧾 No logging                 | Replace `print()` with logging module |

---

# 🚀 Deployment Recommendations

### 🐳 Docker

* Run as lightweight collector
* Mount persistent volume
* Add healthcheck

### 📡 SIEM Integration

* Forward JSON output to:

  * Logstash
  * Fluentd
  * InsightIDR
  * IRIS
  * Splunk HEC

---

# 🧠 Future Enhancements

* 🔄 Pagination support
* 🗂 Multi-tenant handling
* ⚡ Async implementation
* 📊 Severity filtering
* 📁 Persistent state storage
* 🧾 Structured logging

---

# 📌 Conclusion

This project provides:

✅ Secure token handling
✅ Automatic refresh
✅ Dynamic alert querying
✅ Real-time polling
✅ Production-ready architecture

It is suitable for:

* SOC ingestion pipelines
* MSSP collectors
* SIEM enrichment workflows
* Automated incident response systems

---


