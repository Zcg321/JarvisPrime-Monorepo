"""Simple slate simulation to estimate ROI distribution."""
from __future__ import annotations

import json
import random
from typing import List, Dict, Any

from src.data.ownership import load_daily


def run(lineups: List[List[str]], ownership_csv: str, iters: int = 1000, seed: int = 0) -> Dict[str, Any]:
    rng = random.Random(seed)
    ownership = {row["player_id"]: float(row["field_own_pct"]) for row in load_daily(ownership_csv)}
    rois: List[float] = []
    for _ in range(iters):
        total = 0.0
        for lu in lineups:
            score = sum(rng.random() for _ in lu)
            total += score
        rois.append(total)
    rois.sort()
    mean_roi = sum(rois) / len(rois) if rois else 0.0
    p95 = rois[int(0.95 * len(rois)) - 1] if rois else 0.0
    return {
        "roi_distribution": {"mean": mean_roi, "p95": p95},
        "ownership_size": len(ownership),
        "risk_flags": [],
    }
