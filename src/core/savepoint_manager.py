# savepoint_manager.py

import json
import os

SAVEPOINT_FILE = "savepoint.json"

def save_state(metrics):
    with open(SAVEPOINT_FILE, 'w') as f:
        json.dump(metrics, f)
    print("[Savepoint] State saved successfully.")

def load_state():
    if not os.path.exists(SAVEPOINT_FILE):
        print("[Savepoint] No savepoint found.")
        return None
    with open(SAVEPOINT_FILE, 'r') as f:
        metrics = json.load(f)
    print("[Savepoint] State loaded successfully.")
    return metrics
