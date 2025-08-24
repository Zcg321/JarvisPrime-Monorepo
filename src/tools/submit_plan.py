from __future__ import annotations
from typing import List, Dict, Any
from math import floor
from src.reflex.core import Reflex
from src.savepoint.logger import savepoint_log


def submit_plan(slate_id: str, lineups: List[Dict[str, Any]], bankroll: float, unit_fraction: float = 0.02,
                entry_fee: float = 1.0, max_entries: int = 1, seed: int = 0) -> Dict[str, Any]:
    feasible = min(max_entries, len(lineups))
    capacity = floor(bankroll * unit_fraction / entry_fee)
    proposed = min(feasible, capacity)
    total_cost = proposed * entry_fee
    reflex = Reflex()
    decision = {
        "bankroll": bankroll,
        "wager": total_cost,
        "affect": "calm",
        "risk_stats": {"ev": 0.0, "variance": 0.0, "drawdown_p95": 0.0},
    }
    result = reflex.self_check(decision)
    blocked = result.get("blocked", False)
    plan = {
        "proposed_entries": 0 if blocked else proposed,
        "total_cost": 0.0 if blocked else round(total_cost, 2),
        "blocked": blocked,
    }
    if blocked:
        plan["reason"] = result.get("reason", "policy")
    savepoint_log("submit_plan", plan, decision.get("affect"), bankroll)
    return plan
