import os
import yaml
import pickle
from parser import parse_log_line
from featurizer import LogFeaturizer
from sklearn.ensemble import IsolationForest

# If no logs are found in the configured log file, fall back to the
# small in-repo sample logs provided by `test_generator.py` so the
# training script can still run for development/testing.
try:
    from test_generator import NORMAL_LOGS, ANOMALY_LOGS
except Exception:
    NORMAL_LOGS, ANOMALY_LOGS = [], []

def main():
    config = yaml.safe_load(open("config.yaml"))
    log_path = config["log_file"]
    model_path = config["model_path"]

    logs = []
    try:
        # Open log file with a forgiving decoder so non-UTF-8 bytes
        # don't crash the training script. Replace invalid bytes.
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                parsed = parse_log_line(line)
                if parsed:
                    logs.append(parsed)
    except FileNotFoundError:
        logs = []

    if not logs:
        # Fallback to sample logs so the training script is usable even
        # when the configured log file is empty or missing.
        sample_lines = list(NORMAL_LOGS) + list(ANOMALY_LOGS)
        if sample_lines:
            for line in sample_lines:
                parsed = parse_log_line(line)
                if parsed:
                    logs.append(parsed)

    if not logs:
        raise ValueError("❌ No valid log lines parsed. Check your log format or regex.")

    featurizer = LogFeaturizer()
    featurizer.fit(logs)
    X = featurizer.transform(logs)

    if X.size == 0:
        raise ValueError("❌ Feature matrix is empty. Check featurizer or log file content.")

    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump((featurizer, model), f)

    print(f"[OK] Model trained and saved at {model_path}")

if __name__ == "__main__":
    main()
