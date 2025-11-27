import time
import random
import os
from datetime import datetime

LOG_FILE = "sample_logs/access.log"

# Expose sample lines for training fallback
def _build_samples():
    now = datetime.now()
    normal = [
        f'10.0.0.44 - - [{now.strftime("%d/%b/%Y:%H:%M:%S")}] "GET /index HTTP/1.1" 200',
        f'10.0.0.45 - - [{now.strftime("%d/%b/%Y:%H:%M:%S")}] "POST /login HTTP/1.1" 302',
        f'10.0.0.46 - - [{now.strftime("%d/%b/%Y:%H:%M:%S")}] "GET /dashboard HTTP/1.1" 200',
    ]
    anomalies = [
        f'10.0.0.47 - - [{now.strftime("%d/%b/%Y:%H:%M:%S")}] "GET /login?id=\' OR 1=1 --" 500',
        f'10.0.0.48 - - [{now.strftime("%d/%b/%Y:%H:%M:%S")}] "POST /admin/delete_all HTTP/1.1" 500',
    ]
    return normal, anomalies

# Provide module-level constants so train_model.py can import
NORMAL_LOGS, ANOMALY_LOGS = _build_samples()

def generate_log_line():
    """Generate one random log line (normal or anomaly)."""
    # Rebuild to keep timestamps fresh
    normal_logs, anomaly_logs = _build_samples()
    if random.random() < 0.1:
        return random.choice(anomaly_logs)
    return random.choice(normal_logs)

def write_log(line):
    """Append a line to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def main():
    print("🚀 Log generator started. Writing logs to sample_logs/access.log ...\n")
    while True:
        line = generate_log_line()
        write_log(line)
        print(f"[+] Generated: {line}")
        time.sleep(2)

if __name__ == "__main__":
    main()
