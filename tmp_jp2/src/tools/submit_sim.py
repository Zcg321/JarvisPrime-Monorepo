from __future__ import annotations

import random
from typing import Any, Dict

from src.savepoint.logger import savepoint_log
from src.reflex.core import gate_submit_sim


def submit_sim(
    bankroll: float,
    plan: Dict[str, Any],
    iters: int = 1000,
    seed: int = 1337,
    guards: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    entries = plan.get("entries", [])
    results = []
    for _ in range(max(1, iters)):
        gain = 0.0
        for e in entries:
            count = int(e.get("count", 0))
            fee = float(e.get("entry_fee", 0.0))
            for _ in range(max(0, count)):
                roi = rng.gauss(0, 1)
                gain += fee * roi
        results.append(gain)
    n = len(results)
    ev = sum(results) / n
    var = sum((x - ev) ** 2 for x in results) / n
    results.sort()
    p50 = results[int(0.5 * (n - 1))]
    p90 = results[int(0.9 * (n - 1))]
    p_profit = sum(1 for r in results if r > 0) / n
    drawdowns = [max(0.0, -r) / bankroll if bankroll else 0.0 for r in results]
    thr = guards.get("max_drawdown_p95", 1.0) if guards else 1.0
    p_drawdown_gt = sum(d > thr for d in drawdowns) / n
    drawdown_p95 = sorted(drawdowns)[int(0.95 * (n - 1))]
    guards = guards or {}
    violations = []
    if drawdown_p95 > guards.get("max_drawdown_p95", 1.0):
        violations.append("max_drawdown_p95")
    if ev < -bankroll * guards.get("stop_loss", 0.0):
        violations.append("stop_loss")
    if ev > bankroll * guards.get("stop_win", 1.0):
        violations.append("stop_win")
    stats = {
        "ev": ev,
        "var": var,
        "p_drawdown_gt": p_drawdown_gt,
        "p_profit": p_profit,
        "p50": p50,
        "p90": p90,
        "violations": violations[:],
        "blocked": bool(violations),
    }
    risk_viol = gate_submit_sim({"drawdown_p95": drawdown_p95, "variance": var, "ev": ev})
    if risk_viol:
        stats["violations"].extend(risk_viol)
        stats["blocked"] = True
    savepoint_log("post_submit_sim", stats)
    return stats
