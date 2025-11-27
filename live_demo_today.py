#!/usr/bin/env python
"""
Live Real-Time Demo with Today's Date (27/Nov/2025) and Current Time
"""

import subprocess
import time
import os
import sys
import threading
from datetime import datetime
import random

def read_output(pipe):
    """Read and print subprocess output in real-time."""
    for line in pipe:
        print(line.rstrip())

def main():
    print("[DEMO] Real-Time Anomaly Detection - TODAY (27/Nov/2025) Live Time")
    print("=" * 70)
    
    os.makedirs("sample_logs", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    # Clear and prepare
    print("[SETUP] Training model...")
    open("sample_logs/access.log", "w").close()
    result = subprocess.run([sys.executable, "train_model.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr}")
        return
    
    print("[READY] Starting detector...\n")
    
    # Start detector
    detector = subprocess.Popen(
        [sys.executable, "sentinel.py", "--read-all"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1
    )
    
    output_thread = threading.Thread(target=read_output, args=(detector.stdout,))
    output_thread.daemon = True
    output_thread.start()
    
    time.sleep(2)
    
    # Today's date with current live times
    today = datetime.now()
    logs = [
        f'10.0.0.44 - - [{today.strftime("%d/%b/%Y")}:{today.strftime("%H:%M:%S")}] "GET /index HTTP/1.1" 200',
        f'10.0.0.45 - - [{today.strftime("%d/%b/%Y")}:{(today.strftime("%H:%M:%S"))}] "POST /login HTTP/1.1" 302',
        f'10.0.0.46 - - [{today.strftime("%d/%b/%Y")}:{today.strftime("%H:%M:%S")}] "GET /dashboard HTTP/1.1" 200',
        f'10.0.0.47 - - [{today.strftime("%d/%b/%Y")}:{today.strftime("%H:%M:%S")}] "GET /login?id=\' OR 1=1 --" 500',
        f'10.0.0.48 - - [{today.strftime("%d/%b/%Y")}:{today.strftime("%H:%M:%S")}] "POST /admin/delete_all HTTP/1.1" 500',
    ]
    
    print(f"[TIME] Today's date: {today.strftime('%d/%b/%Y')} | Current time: {today.strftime('%H:%M:%S')}\n")
    print("[STREAM] Appending logs with live timestamps...\n")
    
    for i in range(10):
        # Mix normal and anomalies
        if i % 3 == 2:
            log = random.choice(logs[3:5])  # Anomaly
            typ = "ANOMALY"
        else:
            log = random.choice(logs[0:3])  # Normal
            typ = "NORMAL"
        
        with open("sample_logs/access.log", "a", encoding="utf-8") as f:
            f.write(log + "\n")
        
        print(f"[{i+1:2d}] [{typ}] {log}")
        time.sleep(2)
    
    print("\n[WAIT] Detector processing...")
    time.sleep(3)
    
    print("[STOP] Stopping detector...")
    detector.terminate()
    try:
        detector.wait(timeout=3)
    except subprocess.TimeoutExpired:
        detector.kill()
    
    print("\n[DONE] Demo complete!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
