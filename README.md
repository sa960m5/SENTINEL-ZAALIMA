# Sentinel - Real-Time Log Anomaly Detector

A production-ready anomaly detection system for HTTP access logs using machine learning (IsolationForest) with real-time alerts via Slack.

## Features

✅ **Real-Time Monitoring** - Tails log files and processes new entries immediately  
✅ **ML-Based Detection** - IsolationForest for unsupervised anomaly detection  
✅ **Slack Alerts** - Real-time notifications with scores and context  
✅ **Audit Logging** - All detections logged to JSONL for compliance  
✅ **CSV Export** - Export detections for spreadsheet analysis  
✅ **Auto Model Reload** - Picks up new models without restart  
✅ **Alert Cooldown** - Rate-limits alerts to prevent spam  
✅ **Graceful Shutdown** - Clean exit with session statistics  

## Quick Start

### 1. Setup

```powershell
# Activate virtual environment
& "./.venv/Scripts/Activate.ps1"

# Install dependencies
pip install -r requirements.txt
```

### 2. Train Model (One-Time)

```powershell
python train_model.py
```

Reads sample logs, trains IsolationForest, saves to `models/model.pkl`.

### 3. Start Real-Time Detector

```powershell
# Monitor for NEW logs only
python sentinel.py

# OR process all existing logs then monitor for new
python sentinel.py --read-all
```

### 4. Feed Logs

Your app writes to `sample_logs/access.log` (or configure in `config.yaml`), and Sentinel detects anomalies.

Or generate sample logs:

```powershell
python test_generator.py
```

### 5. View Detection Stats

```powershell
# Dashboard with summary and top anomalies
python detection_dashboard.py

# Export to CSV for analysis
python detection_dashboard.py --csv
```

## Configuration

Edit `config.yaml`:

```yaml
log_file: "sample_logs/access.log"       # Log file to monitor
model_path: "models/model.pkl"           # Trained model location
threshold: -0.2                          # Score context (not primary signal)
alert_cooldown: 10                       # Seconds between alerts
slack_webhook: "https://hooks.slack..."  # Slack webhook URL
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Incoming Logs (live append to access.log)               │
└────────────────────┬────────────────────────────────────┘
                     │ tail -f behavior
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Sentinel Detector (sentinel.py)                         │
│  - Parse log lines (parser.py)                          │
│  - Extract features (featurizer.py)                     │
│  - Run ML model inference                               │
│  - Log all results to detections.jsonl                  │
└────────┬──────────────────────────┬──────────────────────┘
         │                          │
     Anomaly                    Normal
    (pred=-1)                 (pred=1)
         │                          │
         ▼                          │
    Rate-limited              [continue]
    (alert_cooldown)           monitoring
         │
         ▼
    Slack Alert (alert.py)
```

## Files

| File | Purpose |
|------|---------|
| `sentinel.py` | Main detector daemon (real-time tailing + detection) |
| `train_model.py` | Model training pipeline |
| `parser.py` | HTTP log line regex parser |
| `featurizer.py` | Feature extraction (TF-IDF + status code) |
| `alert.py` | Slack alert formatting & sending |
| `detection_dashboard.py` | View stats & export CSV |
| `live_demo_today.py` | Demo with today's date/time |
| `test_generator.py` | Generate sample logs |
| `config.yaml` | Configuration |
| `models/model.pkl` | Trained IsolationForest + featurizer |
| `logs/detections.jsonl` | Audit trail (JSONL) |
| `logs/detections.csv` | Exported detections (CSV) |

## Detection Logic

Each log line is scored:

1. **Parse** - Extract IP, timestamp, method, URL, status
2. **Featurize** - TF-IDF on "method URL", plus status code
3. **Predict** - IsolationForest: returns -1 (anomaly) or 1 (normal)
4. **Alert** - If pred=-1 and not rate-limited, send Slack

## Tuning Sensitivity

Edit `train_model.py`:

```python
model = IsolationForest(contamination=0.05, random_state=42)
                        # ↑ Increase for more sensitive
```

Then retrain: `python train_model.py`

Higher `contamination` = more anomalies flagged
Lower `contamination` = only flag rare patterns

## Production Deployment

### Option A: Windows Service

```powershell
# Install NSSM (Non-Sucking Service Manager)
choco install nssm

# Create service
nssm install Sentinel "D:/path/.venv/Scripts/python.exe" "D:/path/sentinel.py"
nssm start Sentinel
```

### Option B: Task Scheduler

Create a scheduled task to run `sentinel.py` on startup with auto-restart.

### Option C: Docker

```dockerfile
FROM python:3.13
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "sentinel.py"]
```

## Monitoring

Check audit logs anytime:

```powershell
# Quick stats
python detection_dashboard.py

# Export for analysis
python detection_dashboard.py --csv

# Tail live logs
Get-Content logs/detections.jsonl -Tail 10 -Wait
```

## Example Output

```
[START] Sentinel Real-Time Anomaly Detector Started
[FILE] Monitoring: sample_logs/access.log
[MODEL] Model: models/model.pkl
[CONFIG] Threshold: -0.2
[ALERT_COOLDOWN] 10.0s
[TIME] Started: 2025-11-27 12:14:28

[ALERT #1] 10.0.0.48 - - [27/Nov/2025:12:14:11] "POST /admin/delete_all HTTP/1.1" 500
   Score: -0.0127 | Threshold: -0.2000
[OK] Slack alert sent!

[OK] 10 logs processed, 1 anomalies detected.
```

## Troubleshooting

**No alerts being sent?**
- Check `slack_webhook` in `config.yaml`
- Test: `python -c "from alert import send_slack_alert; send_slack_alert('Test')"`

**Too many false positives?**
- Increase `contamination` in `train_model.py` and retrain
- Increase `alert_cooldown` to rate-limit more

**Log file not being monitored?**
- Verify `log_file` path in `config.yaml`
- Use `sentinel.py --read-all` to test with existing logs

## License

MIT


## Security
- Do **not** commit your Slack webhook URL to version control. Use environment variables or a local `config.yaml` excluded via `.gitignore`.
