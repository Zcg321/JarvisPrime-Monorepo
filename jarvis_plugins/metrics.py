from __future__ import annotations
import time, threading
from typing import Dict

_START = time.time()
_COUNTERS: Dict[str, int] = {}
_LOCK = threading.Lock()

def inc(key: str, n: int = 1):
    with _LOCK:
        _COUNTERS[key] = _COUNTERS.get(key, 0) + n

def snapshot() -> Dict[str, object]:
    with _LOCK:
        return {
            "uptime_sec": int(time.time() - _START),
            "counters": dict(_COUNTERS),
        }
