---

# 🛡️ Cynet 360 Real-Time Alerts Collector

A high-performance, stateful Python collector engineered to interface with the **Cynet 360 Security Platform**. This tool automates the authentication handshake, manages token lifecycles with proactive refreshing, and implements a cursor-based polling mechanism for real-time alert ingestion.

---

## 📖 Table of Contents

* [✨ Features](https://www.google.com/search?q=%23-features)
* [⚙️ Tech Stack](https://www.google.com/search?q=%23%EF%B8%8F-tech-stack)
* [📂 Project Architecture](https://www.google.com/search?q=%23-project-architecture)
* [🚀 Installation & Setup](https://www.google.com/search?q=%23-installation--setup)
* [🔍 Code Logic Breakdown](https://www.google.com/search?q=%23-code-logic-breakdown)
* [🛠 Security Best Practices](https://www.google.com/search?q=%23-security-best-practices)
* [📈 Deployment Strategy](https://www.google.com/search?q=%23-deployment-strategy)

---

## ✨ Features

* **🔄 Self-Healing Auth:** Automatically detects `401 Unauthorized` errors and re-authenticates.
* **⏰ Proactive Token Refresh:** Refreshes the 60-minute JWT 5 minutes before expiration to prevent race conditions.
* **📍 Cursor-Based Polling:** Uses the `LastSeen` parameter to ensure 0% data overlap and 100% alert coverage.
* **📉 Zero Dependencies:** Uses standard Python libraries (`http.client`) for maximum compatibility and minimal attack surface.

---

## ⚙️ Tech Stack

* **Language:**
* **Protocol:**
* **Format:**
* **Architecture:** Singleton Client Pattern

---

## 📂 Project Architecture

The logic follows a **Circular Polling Pattern**:

1. **Identity Provider (IdP):** Exchanges credentials for a scoped Bearer Token.
2. **Validation Gate:** Checks `token_expiry` before every API call.
3. **Data Fetcher:** Requests alerts since `LastSeen`.
4. **State Update:** Advances the `LastSeen` cursor to `now()`.
5. **Backoff:** Sleeps for 60 seconds to respect API rate limits.

---

## 🔍 Code Logic Breakdown

Below is the line-by-line surgical breakdown of the collector's core logic.

### 1. Configuration & Constants

```python
POLL_INTERVAL = 60      # Frequency of alert checks (in seconds)
TOKEN_BUFFER = 55 * 60  # Safety window: refresh token after 55 mins (API limit is 60)

```

### 2. The `CynetClient` Initialization

* `self.access_token`: Stores the active JWT.
* `self.token_expiry`: A Unix timestamp calculating when the token becomes "stale."
* `self.last_seen`: Initialized to `UTC - 24h` to ensure the first run captures recent historical data.

### 3. `authenticate(self)`

* **Lines 30-40:** Establishes an `HTTPSConnection` to your specific Cynet domain.
* **Lines 42-45:** Packages `user_name` and `password` into a JSON string.
* **Lines 53-56:** Parses the response. It extracts the `access_token` and sets the `token_expiry` by adding the 55-minute buffer to the current time.

### 4. `ensure_token(self)`

* **Logic:** This is the "Safety Guard." It evaluates: `if current_time >= token_expiry`. If true, it triggers `authenticate()` *before* the API is polled, preventing failed requests.

### 5. `get_alerts(self)`

* **Timestamp Formatting:** Converts Python `datetime` objects into the specific string format Cynet requires: `YYYY-MM-DD hh:mm:ss`.
* **URL Encoding:** Uses `urllib.parse.urlencode` to ensure the timestamp string is safe for HTTP transmission (handling spaces and colons).
* **Headers:** Injects the `client_id` and the `access_token` into the request headers for authorization.
* **Recursive Retry:** If a `401` status is returned (unexpected expiration), the function calls itself once more to retry after a fresh login.

### 6. The Main Loop

```python
while True:
    alerts = client.get_alerts() # Fetches data
    # ... process alerts ...
    time.sleep(POLL_INTERVAL)    # Pauses to prevent API throttling

```

---

## 🛠 Security Best Practices

> [!WARNING]
> **Never commit your credentials to Version Control (Git).**

| Risk | Mitigation |
| --- | --- |
| **Credential Leak** | Use a `.env` file and `os.environ.get()` |
| **Memory Exhaustion** | The script processes alerts in stream; ensure your SIEM can handle the volume |
| **Data Loss** | Persist the `last_seen` value to a local `state.json` file so it survives script restarts |

---

## 📈 Deployment Strategy

### 🐳 Dockerize (Recommended)

Deploying as a container ensures the environment is isolated and the collector stays running 24/7.

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY collector.py .
CMD ["python", "collector.py"]

```

### 🖥️ SIEM Ingestion

To send these alerts to a SIEM (Splunk, Sentinel, ELK), replace the `print(json.dumps(alerts))` line with a POST request to your SIEM's **HTTP Event Collector (HEC)** or write to a watched log file.

---

## 📌 Conclusion

This collector provides a production-grade bridge between Cynet 360 and your security operations center. By managing the complexities of OAuth2-style flows and time-based filtering, it allows security engineers to focus on **threat hunting** rather than **data plumbing**.

**Version:** 1.0.0
**Purpose:** Automated Threat Ingestion

---
