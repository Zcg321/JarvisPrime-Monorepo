"""DFS engine wrappers.

MIT License.
Copyright (c) 2025 Zack
"""
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from .dfs import predict_lineup, roi as roi
from . import dfs_roi_memory as roi_memory
from . import dfs_metrics

GHOST_FILE = Path("logs/dfs_ghosts.jsonl")


def _apply_roi_bias(players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Adjust projections using rolling z-scores from ROI memory."""
    z = roi_memory.rolling_zscores()
    biased = []
    for p in players:
        bias = z.get(p.get("name"), 0.0)
        proj = p.get("proj", 0.0) * (1 + 0.05 * bias)
        biased.append({**p, "proj": proj})
    return biased


def lineup(players: List[Dict[str, Any]], budget: float, roster: Optional[Dict[str, int]] = None):
    """Greedy lineup generator with ROI bias."""
    players = _apply_roi_bias(players)
    return predict_lineup(players, budget, roster)


def lineup_pool(
    players: List[Dict[str, Any]],
    budget: float,
    n: int = 20,
    roster: Optional[Dict[str, int]] = None,
    seed: Optional[int] = None,
):
    """Generate a pool of lineups using stochastic shuffles and ghost injection."""
    random.seed(seed)
    pool = []
    for _ in range(n):
        random.shuffle(players)
        pool.append(predict_lineup(players, budget, roster)["lineup"])

    ghosts = _load_ghosts(min(3, n))
    for g in ghosts:
        pool.append(_mutate_lineup(g, players, budget, roster))
    return pool


def _load_ghosts(k: int) -> List[List[Dict[str, Any]]]:
    if not GHOST_FILE.exists():
        return []
    lines = [json.loads(l) for l in GHOST_FILE.read_text().splitlines() if l.strip()]
    lines.sort(key=lambda x: x.get("ev", 0), reverse=True)
    return [l.get("lineup", []) for l in lines[:k]]


def _mutate_lineup(base_lineup: List[Dict[str, Any]], players: List[Dict[str, Any]], budget: float, roster: Optional[Dict[str, int]]):
    if not base_lineup:
        return predict_lineup(players, budget, roster)["lineup"]
    names = {p["name"] for p in base_lineup}
    remaining = [p for p in players if p["name"] not in names]
    if remaining:
        idx = random.randrange(len(base_lineup))
        base_lineup[idx] = remaining[0]
    res = predict_lineup(base_lineup + remaining, budget, roster)
    return res["lineup"]


def record_result(lineup: List[str], entry_fee: float, winnings: float):
    """Record ROI result for future biasing."""
    return roi_memory.record_result(lineup, entry_fee, winnings)


def showdown_lineup(players: List[Dict[str, Any]], budget: float, seed: Optional[int] = None):
    """Build a showdown lineup with a captain (1.5x cost/proj) and 5 flex spots."""
    random.seed(seed)
    players = _apply_roi_bias(players)
    for captain in sorted(players, key=lambda x: x.get("proj", 0) / max(x.get("cost", 1), 1), reverse=True):
        c_cost = captain["cost"] * 1.5
        if c_cost > budget:
            continue
        remaining = [p for p in players if p["name"] != captain["name"]]
        res = predict_lineup(remaining, budget - c_cost, {"FLEX": 5})
        if len(res["lineup"]) == 5:
            lineup = [
                {**captain, "slot": "CPT", "cost": c_cost, "proj": captain["proj"] * 1.5}
            ] + [{**p, "slot": "FLEX"} for p in res["lineup"]]
            return {
                "lineup": lineup,
                "cost": c_cost + res["cost"],
                "expected": captain["proj"] * 1.5 + res["expected"],
            }
    return {"lineup": [], "cost": 0.0, "expected": 0.0}


def apply_calibration(
    players: List[Dict[str, Any]],
    alpha: float = 0.08,
    beta: float = 0.05,
    gamma: float = 0.04,
    seed: Optional[int] = None,
):
    """Calibrate projections using ROI z-scores, uniqueness, and risk."""
    rng = random.Random(seed)
    z = roi_memory.rolling_zscores(window=100)
    uniq = dfs_metrics.uniqueness_score(players)
    calibrated = []
    for p in players:
        z_roi = z.get(p.get("name"), 0.0)
        u = uniq.get(p.get("name"), 0.0)
        r = p.get("risk", dfs_metrics.risk_score([p]))
        proj = p.get("proj", 0.0) * (1 + alpha * z_roi + beta * u - gamma * r)
        calibrated.append({**p, "proj": proj})
    rng.shuffle(calibrated)
    return calibrated

