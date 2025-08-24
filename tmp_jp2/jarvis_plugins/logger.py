from __future__ import annotations
import os, json, time
from pathlib import Path

LOG_DIR = Path(os.getenv("JARVIS_LOG_DIR", "artifacts/logs")).resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "jarvis.log"

def log(event: str, payload: dict):
    row = {"ts": time.time(), "event": event, "payload": payload}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
