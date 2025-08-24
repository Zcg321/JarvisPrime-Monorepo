"""Generate ROI attribution reports from ghost logs."""
from __future__ import annotations

import json
import os
from typing import Dict, Any, List


def generate(lookback_days: int = 60, log_path: str = "logs/ghosts/roi.jsonl") -> Dict[str, Any]:
    if not os.path.exists(log_path):
        return {"top": [], "bottom": []}
    agg: Dict[str, List[float]] = {}
    with open(log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            pid = rec.get("player_id")
            roi = float(rec.get("roi", 0.0))
            if pid is None:
                continue
            agg.setdefault(pid, []).append(roi)
    averages = [(sum(v) / len(v), pid) for pid, v in agg.items() if v]
    averages.sort(reverse=True)
    top = [{"player_id": pid, "roi": round(avg, 4)} for avg, pid in averages[:5]]
    bottom = [{"player_id": pid, "roi": round(avg, 4)} for avg, pid in averages[-5:]]
    return {"top": top, "bottom": bottom}
