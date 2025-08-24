from __future__ import annotations

import random
from typing import Any, Dict, List

from src.reflex import policy as risk_policy
from src.savepoint import logger as savepoint_logger
from src.reflex.core import risk_check


def optimize(
    bankroll: float,
    contests: List[Dict[str, Any]],
    kelly_fraction: float = 0.25,
    drawdown_guard_p95: float = 0.25,
    seed: int = 1337,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    plan = []
    total = 0.0
    ev_sum = 0.0
    var_sum = 0.0
    drawdown = 0.0
    for c in contests:
        iters = int(c.get("iters", 1000))
        rois = [rng.gauss(0, 0.1) for _ in range(max(1, iters))]
        ev = sum(rois) / iters
        var = sum((x - ev) ** 2 for x in rois) / iters
        dd = abs(sorted(rois)[int(0.05 * (iters - 1))])
        kelly = ev / var if var else 0.0
        entries = min(
            int((bankroll * kelly_fraction * max(kelly, 0)) / c["entry_fee"]),
            int(c.get("max_entries", 1)),
        )
        spend = entries * c["entry_fee"]
        total += spend
        ev_sum += ev
        var_sum += var
        drawdown = max(drawdown, dd)
        plan.append({"slate_id": c["slate_id"], "entries": entries, "spend": spend})
    risk_stats = {
        "ev": ev_sum,
        "variance": var_sum,
        "drawdown_p95": drawdown,
    }
    risk_check(risk_stats)
    if drawdown > drawdown_guard_p95:
        raise risk_policy.RiskViolation("risk_policy")
    leftover = bankroll - total
    savepoint_logger.savepoint_log("post_bankroll_ev", {"plan": plan}, None, None)
    return {"plan": plan, "leftover": leftover, "risk_stats": risk_stats}
