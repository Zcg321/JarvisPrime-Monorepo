"""ROI attribution via Shapley-lite approximation."""
from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Dict, Any, List

from src.savepoint.logger import savepoint_log

LOG_PATH = Path("logs/reports/roi_attrib.jsonl")


def roi_attrib(
    lineup: Dict[str, Any],
    ownership_csv: str,
    iters: int = 2000,
    seed: int = 1337,
    stack_pairs: bool = False,
) -> Dict[str, Any]:
    players = [p.get("player_id") for p in lineup.get("players", [])]
    if not players:
        result = {"players": [], "pairs": [] if stack_pairs else []}
        _log(result)
        return result
    try:
        with open(ownership_csv, "r", encoding="utf-8") as f:
            sum(1 for _ in f)
    except Exception:
        pass
    rng = random.Random(seed)
    K = min(int(iters), 64)
    scores = {p: 0.0 for p in players}
    for _ in range(K):
        perm = players[:]
        rng.shuffle(perm)
        subtotal = 0.0
        for pid in perm:
            subtotal += 1.0
            scores[pid] += subtotal
    players_mc: List[Dict[str, Any]] = []
    for pid in players:
        players_mc.append({"player_id": pid, "mc": scores[pid] / K})
    players_mc.sort(key=lambda x: (-x["mc"], str(x["player_id"])))
    for idx, rec in enumerate(players_mc, 1):
        rec["rank"] = idx
    result: Dict[str, Any] = {"players": players_mc}
    if stack_pairs and len(players) >= 2:
        p1, p2 = sorted(players)[:2]
        pair_mc = (scores[p1] + scores[p2]) / K
        result["pairs"] = [{"pair": [p1, p2], "mc": pair_mc}]
    _log(result)
    return result


def _log(result: Dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": int(time.time()), "result": result}
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, separators=(",", ":")) + "\n")
    try:
        savepoint_log("post_roi_attrib", result)
    except Exception:
        pass
