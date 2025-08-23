"""Accessors for Reflex bias store.

MIT License.
Copyright (c) 2025 Zack
"""
import json
from src.reflex.core import BIAS_FILE

def load() -> dict:
    try:
        return json.loads(BIAS_FILE.read_text())
    except Exception:
        return {}

def save(data: dict) -> None:
    BIAS_FILE.parent.mkdir(parents=True, exist_ok=True)
    BIAS_FILE.write_text(json.dumps(data))
