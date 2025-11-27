import yaml
import time
import pickle
import signal
import sys
import os
import json
from datetime import datetime
from parser import parse_log_line
from alert import send_slack_alert, format_anomaly_alert

class RealTimeAnomalyDetector:
    def __init__(self):
        self.running = True
        self.anomalies_detected = 0
        self.logs_processed = 0
        self.normal_count = 0
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        self.audit_log = "logs/detections.jsonl"
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
    
    def _shutdown_handler(self, signum, frame):
        """Handle graceful shutdown on Ctrl+C or SIGTERM."""
        print("\n\n[STOP] Shutting down Sentinel...")
        print(f"[STATS] Session Statistics:")
        print(f"    - Logs Processed: {self.logs_processed}")
        print(f"    - Normal: {self.normal_count}")
        print(f"    - Anomalies Detected: {self.anomalies_detected}")
        if self.logs_processed > 0:
            pct = (self.anomalies_detected / self.logs_processed) * 100
            print(f"    - Anomaly Rate: {pct:.1f}%")
        print(f"[LOG] Audit log: {self.audit_log}")
        self.running = False
        sys.exit(0)
    
    def _log_detection(self, log_line: str, score: float, pred: int, timestamp: str = ""):
        """Log detection to JSONL audit file."""
        try:
            record = {
                "timestamp": timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "log_line": log_line,
                "score": round(score, 4),
                "prediction": pred,
                "label": "anomaly" if pred == -1 else "normal"
            }
            with open(self.audit_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to log detection: {e}")
    
    def tail_log(self, file_path, read_all=False):
        """Tail a log file in real-time, yielding new lines as they arrive."""
        try:
            # Detect file encoding by reading the first few bytes for BOM
            with open(file_path, "rb") as f:
                head = f.read(4)
            
            if head.startswith(b'\xff\xfe'):
                enc = 'utf-16-le'
            elif head.startswith(b'\xfe\xff'):
                enc = 'utf-16-be'
            elif head.startswith(b'\xef\xbb\xbf'):
                enc = 'utf-8-sig'
            else:
                enc = 'utf-8'
            
            with open(file_path, "r", encoding=enc, errors="replace") as f:
                # Start at beginning if read_all is True, else at end
                if not read_all:
                    f.seek(0, 2)
                
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    yield line.strip()
        except FileNotFoundError:
            print(f"[ERROR] Log file not found: {file_path}")
            self.running = False
        except Exception as e:
            print(f"[ERROR] Error reading log file: {e}")
            self.running = False
    
    def detect(self, log_path, model_path, threshold, read_all=False):
        """Load model and begin real-time anomaly detection.

        Improvements in this iteration:
        - Use `model.predict` for robust anomaly decisions (predict == -1).
        - Keep `decision_function` score for context in alerts.
        - Auto-reload model if the model file changes on disk.
        - Rate-limit alerts with a cooldown (configurable).
        """
        # Validate files exist
        if not os.path.exists(model_path):
            print(f"[ERROR] Model file not found: {model_path}")
            print(f"    Run 'python train_model.py' first to train the model.")
            return

        if not os.path.exists(log_path):
            print(f"[ERROR] Log file not found: {log_path}")
            return

        # Load trained model and featurizer
        try:
            with open(model_path, "rb") as f:
                featurizer, model = pickle.load(f)
            model_mtime = os.path.getmtime(model_path)
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            return

        # Alert rate-limiting (seconds)
        alert_cooldown = 10.0
        try:
            cfg = yaml.safe_load(open("config.yaml"))
            alert_cooldown = float(cfg.get("alert_cooldown", alert_cooldown))
        except Exception:
            pass
        last_alert_time = 0.0

        print(f"\n[START] Sentinel Real-Time Anomaly Detector Started")
        print(f"[FILE] Monitoring: {log_path}")
        print(f"[MODEL] Model: {model_path}")
        print(f"[CONFIG] Threshold: {threshold}")
        print(f"[MODE] Reading: {'all logs' if read_all else 'new logs only'}")
        print(f"[ALERT_COOLDOWN] {alert_cooldown}s")
        print(f"[TIME] Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[HINT] Press Ctrl+C to stop.\n")

        for line in self.tail_log(log_path, read_all=read_all):
            if not self.running:
                break

            # Auto-reload model if the file changed
            try:
                current_mtime = os.path.getmtime(model_path)
                if current_mtime != model_mtime:
                    with open(model_path, "rb") as f:
                        featurizer, model = pickle.load(f)
                    model_mtime = current_mtime
                    print(f"[INFO] Model reloaded at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception:
                pass

            # Parse log line
            parsed = parse_log_line(line)
            if not parsed:
                print(f"[WARN] Failed to parse: {line}")
                continue

            self.logs_processed += 1

            # Extract features and get anomaly score/prediction
            try:
                features = featurizer.transform([parsed])
                score = float(model.decision_function(features)[0])
                pred = int(model.predict(features)[0])
            except Exception as e:
                print(f"[WARN] Error processing features: {e}")
                continue

            # Use both model.predict and the decision_function score for
            # anomaly detection. Relying only on `predict` can miss
            # anomalous-looking lines when the IsolationForest's
            # contamination parameter is low or the training set is small.
            # Treat as anomaly if either the model predicts -1 or the
            # decision score is below the configured threshold.
            is_anomaly = (pred == -1) or (score < threshold)

            # Check if anomaly
            if is_anomaly:
                now = time.time()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Log detection before cooldown check
                self._log_detection(line, score, -1, timestamp=timestamp)
                
                if now - last_alert_time < alert_cooldown:
                    # skip alert due to cooldown, but count it
                    self.anomalies_detected += 1
                    continue

                self.anomalies_detected += 1
                last_alert_time = now
                alert_msg = format_anomaly_alert(line, score, threshold, timestamp)

                print(f"\n[ALERT #{self.anomalies_detected}] {line}")
                print(f"   Score: {score:.4f} | Threshold: {threshold:.4f}")

                # Send Slack alert
                send_slack_alert(alert_msg)
                print()
            else:
                # Normal log
                self.normal_count += 1
                self._log_detection(line, score, 1, timestamp="")
                # Show summary every N logs
                if self.logs_processed % 10 == 0:
                    print(f"[OK] {self.logs_processed} logs processed, {self.anomalies_detected} anomalies detected.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sentinel Real-Time Log Anomaly Detector")
    parser.add_argument("--read-all", action="store_true", help="Read all existing logs (default: new logs only)")
    args = parser.parse_args()
    
    try:
        config = yaml.safe_load(open("config.yaml"))
        log_path = config.get("log_file", "sample_logs/access.log")
        model_path = config.get("model_path", "models/model.pkl")
        threshold = config.get("threshold", -0.2)
        
        detector = RealTimeAnomalyDetector()
        detector.detect(log_path, model_path, threshold, read_all=args.read_all)
    
    except FileNotFoundError:
        print("[ERROR] config.yaml not found. Please ensure it exists in the project root.")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    main()
