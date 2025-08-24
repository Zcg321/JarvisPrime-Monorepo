from __future__ import annotations

from typing import Any, Dict, List

from src.tools.submit_sim import submit_sim
from src.tools.portfolio_dedupe import portfolio_dedupe
from src.savepoint.logger import savepoint_log


def submit_plan(
    date: str,
    site: str,
    modes: List[str],
    n_lineups: int,
    max_from_team: int,
    seed: int,
    as_plan: bool,
    bankroll: float,
    unit_fraction: float,
    entry_fee: float,
    max_entries: int,
) -> Dict[str, Any]:
    """Build a trivial submission plan and simulate it.

    This minimal implementation does not perform real lineup generation; it
    merely constructs a deterministic plan based on the requested counts and
    invokes :func:`submit_sim` to obtain a seeded EV preview.
    """

    lineups = [{"id": f"L{i}", "players": [{"player_id": f"P{i}"}]} for i in range(n_lineups)]
    ded = portfolio_dedupe(lineups, max_dupe=1, min_hamming=1, seed=seed)
    kept_ids = ded["kept_ids"]
    kept = [lu for lu in lineups if lu["id"] in kept_ids]
    entries = [
        {
            "slate_id": f"{site}_{date}_MAIN",
            "type": modes[0] if modes else "classic",
            "count": min(len(kept), max_entries),
            "entry_fee": entry_fee,
        }
    ]
    plan = {"lineups": kept, "entries": entries}
    sim = submit_sim(
        bankroll=bankroll,
        plan={"entries": entries},
        iters=500,
        seed=seed,
        guards={"max_drawdown_p95": 0.25},
    )
    status = "blocked" if sim.get("violations") else "ok"
    savepoint_log(
        "post_submit_plan",
        {
            "lineup_ids": kept_ids,
            "plan_summary": {"entries": len(entries), "lineups": len(kept_ids)},
            "sim_summary": {"ev": sim.get("ev"), "violations": sim.get("violations", [])},
            "status": status,
        },
    )
    return {"plan": plan, "sim": sim, "status": status}
