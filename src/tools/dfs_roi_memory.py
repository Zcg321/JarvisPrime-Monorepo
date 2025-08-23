"""ROI memory store.

MIT License (c) 2025 Zack
"""
import json
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

LOG_PATH = Path("logs/dfs_roi.jsonl")


def record_result(lineup, entry_fee, winnings):
    """Persist a DFS result and return stored object."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    net = winnings - entry_fee
    roi = (net / entry_fee) if entry_fee else 0.0
    obj = {
        "ts": time.time(),
        "lineup": lineup,
        "entry_fee": entry_fee,
        "winnings": winnings,
        "net": net,
        "roi": roi,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")
    return obj


def _load():
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def player_scores():
    data = _load()
    scores = defaultdict(list)
    for entry in data:
        net = entry["net"]
        lineup = entry.get("lineup", [])
        share = net / len(lineup) if lineup else 0.0
        for p in lineup:
            scores[p].append(share)
    return {p: sum(vals) for p, vals in scores.items()}


def lineup_scores():
    return [e["roi"] for e in _load()]


def rolling_zscores(window=5):
    data = _load()[-window:]
    values = defaultdict(list)
    for entry in data:
        net = entry["net"]
        lineup = entry.get("lineup", [])
        share = net / len(lineup) if lineup else 0.0
        for p in lineup:
            values[p].append(share)
    z = {}
    for p, vals in values.items():
        if len(vals) > 1:
            m = mean(vals)
            s = stdev(vals)
            z[p] = (vals[-1] - m) / s if s else 0.0
        else:
            z[p] = 0.0
    return z
