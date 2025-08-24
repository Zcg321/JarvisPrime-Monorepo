"""Autoscale hints based on metrics rollups."""

import json
from pathlib import Path
from typing import Dict, Any

from src.config.loader import load_config

ROLLUP_PATH = Path("logs/metrics/rollup_hourly.jsonl")
CFG = load_config().get("metrics", {}).get("autoscale", {})


def _latest() -> Dict[str, Any] | None:
    if not ROLLUP_PATH.exists():
        return None
    last = None
    with ROLLUP_PATH.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = json.loads(line)
    return last


def hint() -> Dict[str, Any]:
    roll = _latest()
    if not roll:
        return {"scale": "hold", "reason": "no_data"}
    count = roll.get("count", 0)
    rps = count / 60.0
    p95 = roll.get("p95_ms", 0)
    up = CFG.get("up", {})
    down = CFG.get("down", {})
    if up and (rps > up.get("rps", float("inf")) or p95 > up.get("p95_ms", float("inf"))):
        return {"scale": "up", "reason": f"rps={rps:.2f},p95={p95}"}
    if down and (rps < down.get("rps", 0) and p95 < down.get("p95_ms", float("inf"))):
        return {"scale": "down", "reason": f"rps={rps:.2f},p95={p95}"}
    return {"scale": "hold", "reason": "within_thresholds"}
