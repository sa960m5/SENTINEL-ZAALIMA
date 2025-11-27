import requests
import yaml
from datetime import datetime

WEBHOOK_CACHE = None

def _get_webhook():
    global WEBHOOK_CACHE
    if WEBHOOK_CACHE is not None:
        return WEBHOOK_CACHE
    try:
        cfg = yaml.safe_load(open("config.yaml"))
        WEBHOOK_CACHE = cfg.get("slack_webhook")
    except Exception:
        WEBHOOK_CACHE = None
    return WEBHOOK_CACHE

def send_slack_alert(message: str):
    webhook_url = _get_webhook()
    if not webhook_url:
        print("[WARN] Slack webhook not configured. Skipping alert.")
        return

    payload = {"text": f"*[ALERT]* Sentinel Anomaly Detected\n{message}"}
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code == 200:
            print("[OK] Slack alert sent!")
        else:
            print(f"[FAIL] Slack alert failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Slack connection error: {e}")

def format_anomaly_alert(log_line: str, anomaly_score: float, threshold: float, timestamp: str = None):
    """Format a rich anomaly alert message with context."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    severity = "CRITICAL" if anomaly_score < (threshold * 0.8) else "HIGH"
    message = f"""*[{severity}]* Anomaly Detected
*Timestamp:* {timestamp}
*Log Line:* ```{log_line}```
*Anomaly Score:* {anomaly_score:.4f}
*Threshold:* {threshold:.4f}
*Deviation:* {abs(anomaly_score - threshold):.4f}
    """.strip()
    return message
