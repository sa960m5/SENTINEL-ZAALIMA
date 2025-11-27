#!/usr/bin/env python
"""
Detection Summary Dashboard - View audit logs and statistics
"""

import json
import sys
from datetime import datetime
from collections import defaultdict

def load_detections(audit_log="logs/detections.jsonl"):
    """Load all detections from JSONL audit log."""
    detections = []
    try:
        with open(audit_log, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        detections.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        print(f"[ERROR] Audit log not found: {audit_log}")
        return []
    return detections

def show_summary(detections):
    """Print summary statistics."""
    if not detections:
        print("[INFO] No detections yet.")
        return
    
    total = len(detections)
    anomalies = sum(1 for d in detections if d.get("label") == "anomaly")
    normal = total - anomalies
    
    print(f"\n[SUMMARY] Detection Statistics")
    print(f"{'='*60}")
    print(f"Total Logs Processed:  {total}")
    print(f"Normal Logs:           {normal} ({normal*100//total if total else 0}%)")
    print(f"Anomalies Detected:    {anomalies} ({anomalies*100//total if total else 0}%)")
    print(f"Anomaly Rate:          {anomalies/total*100:.1f}%")

def show_anomalies(detections, limit=20):
    """Show recent anomalies."""
    anomalies = [d for d in detections if d.get("label") == "anomaly"]
    if not anomalies:
        print("\n[INFO] No anomalies detected yet.")
        return
    
    print(f"\n[ANOMALIES] Last {min(limit, len(anomalies))} Detected")
    print(f"{'='*60}")
    for i, det in enumerate(anomalies[-limit:], 1):
        ts = det.get("timestamp", "N/A")
        score = det.get("score", 0)
        line = det.get("log_line", "")[:70]
        print(f"{i:3d}. [{ts}] Score: {score:7.4f}  {line}")

def show_top_anomalous(detections, limit=10):
    """Show top anomalous log patterns."""
    anomalies = [d for d in detections if d.get("label") == "anomaly"]
    if not anomalies:
        return
    
    # Group by log line pattern
    patterns = defaultdict(list)
    for det in anomalies:
        line = det.get("log_line", "")
        patterns[line].append(det.get("score", 0))
    
    # Sort by frequency
    top = sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True)[:limit]
    
    print(f"\n[TOP ANOMALIES] Most Frequent Patterns ({limit} shown)")
    print(f"{'='*60}")
    for i, (pattern, scores) in enumerate(top, 1):
        count = len(scores)
        avg_score = sum(scores) / count
        print(f"{i:3d}. Count: {count:3d}  Avg Score: {avg_score:7.4f}")
        print(f"     {pattern[:75]}")

def export_csv(detections, output_file="logs/detections.csv"):
    """Export detections to CSV."""
    try:
        import csv
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            if detections:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "log_line", "score", "prediction", "label"])
                writer.writeheader()
                writer.writerows(detections)
        print(f"\n[EXPORT] Detections exported to {output_file}")
    except Exception as e:
        print(f"[ERROR] Export failed: {e}")

def main():
    audit_log = "logs/detections.jsonl"
    
    print(f"\n[DASHBOARD] Sentinel Detection Audit")
    print(f"Audit log: {audit_log}")
    
    detections = load_detections(audit_log)
    
    show_summary(detections)
    show_anomalies(detections, limit=15)
    show_top_anomalous(detections, limit=10)
    
    # Optional CSV export
    if "--csv" in sys.argv:
        export_csv(detections)
    
    print("\n[USAGE] python detection_dashboard.py [--csv]")
    print("        --csv : Export detections to CSV\n")

if __name__ == "__main__":
    main()
