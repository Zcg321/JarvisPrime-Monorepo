"""Portfolio A/B evaluator."""

import csv
import random
from typing import Dict, List, Any

from src.savepoint.logger import savepoint_log


def _simulate(lineups: List[List[float]], rng: random.Random, iters: int):
    scores = []
    for _ in range(iters):
        lineup = rng.choice(lineups) if lineups else []
        base = sum(lineup)
        noise = rng.gauss(0, 1)
        score = base + noise
        scores.append(score)
    avg = sum(scores) / iters if iters else 0.0
    var = sum((s - avg) ** 2 for s in scores) / iters if iters else 0.0
    return scores, avg, var


def portfolio_ab(
    A: Dict[str, Any],
    B: Dict[str, Any],
    ownership_csv: str,
    iters: int = 5000,
    seed: int = 1337,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    # ownership_csv currently ignored but ensures deterministic seed when read
    try:
        with open(ownership_csv, newline="") as f:
            sum(1 for _ in csv.reader(f))
    except Exception:
        pass
    scoresA, avgA, varA = _simulate(A.get("lineups", []), rng, iters)
    scoresB, avgB, varB = _simulate(B.get("lineups", []), rng, iters)
    winsB = sum(1 for a, b in zip(scoresA, scoresB) if b > a) / iters if iters else 0.0
    lift = avgB - avgA
    result = {
        "lift_ev": lift,
        "p_win": winsB,
        "summary": {"A": {"avg": avgA, "var": varA}, "B": {"avg": avgB, "var": varB}},
    }
    try:
        savepoint_log("post_portfolio_ab", result)
    except Exception:
        pass
    return result
