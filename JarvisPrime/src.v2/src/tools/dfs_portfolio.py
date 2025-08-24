"""Portfolio builder across multiple slates with exposure caps."""
from __future__ import annotations

from typing import Dict, Any, List, Optional

from src.savepoint.logger import savepoint_log
from . import ghost_dfs
from . import submit_plan as submit_plan_tool


def build(
    slates: List[Dict[str, str]],
    n_lineups: int,
    max_from_team: int = 3,
    global_exposure_caps: Optional[Dict[str, float]] = None,
    scoring_mode: str = "gohan",
    seed: int = 0,
    objectives: Optional[Dict[str, float]] = None,
    as_plan: bool = False,
    bankroll: Optional[float] = None,
    unit_fraction: Optional[float] = None,
    entry_fee: Optional[float] = None,
    max_entries: Optional[int] = None,
) -> Dict[str, Any]:
    pool: List[Dict[str, Any]] = []
    for idx, slate in enumerate(slates):
        sid = slate.get("id", f"S{idx}")
        for item in ghost_dfs.seed_pool(sid, seed + idx, pool_size=max(n_lineups * 3, 1)):
            item["slate_id"] = sid
            pool.append(item)
    selected: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    slate_alloc: Dict[str, int] = {}
    caps = global_exposure_caps or {}
    for item in pool:
        if len(selected) >= n_lineups:
            break
        lineup = item["players"]
        teams: Dict[str, int] = {}
        players: List[str] = []
        for p in lineup:
            pid = p.get("player") or p.get("name") or ""
            team = p.get("team") or f"T{hash(pid)%10}"
            teams[team] = teams.get(team, 0) + 1
            players.append(pid)
        if teams and max(teams.values()) > max_from_team:
            continue
        ok = True
        for pid in players:
            cap = caps.get(pid)
            if cap is not None and counts.get(pid, 0) + 1 > cap * n_lineups:
                ok = False
                break
        if not ok:
            continue
        selected.append(item)
        slate_id = item.get("slate_id", "")
        slate_alloc[slate_id] = slate_alloc.get(slate_id, 0) + 1
        for pid in players:
            counts[pid] = counts.get(pid, 0) + 1
    from . import dfs_portfolio_opt
    if objectives:
        selected = dfs_portfolio_opt.optimize(selected, objectives, seed)

    exposure_report = {
        pid: {"count": c, "exposure": c / len(selected) if selected else 0.0}
        for pid, c in counts.items()
    }
    slate_allocations = [
        {"slate_id": sid, "lineups": cnt} for sid, cnt in slate_alloc.items()
    ]
    leftovers = [item.get("leftover", 0) for item in selected]
    if leftovers:
        leftovers_sorted = sorted(leftovers)
        mean_left = int(sum(leftovers_sorted) / len(leftovers_sorted))
        p95_idx = max(int(len(leftovers_sorted) * 0.95) - 1, 0)
        p95 = int(leftovers_sorted[p95_idx])
        max_left = int(leftovers_sorted[-1])
    else:
        mean_left = p95 = max_left = 0
    leftover_stats = {"mean": mean_left, "p95": p95, "max": max_left}
    savepoint_log(
        "post_portfolio_build",
        {
            "exposure_report": exposure_report,
            "slate_allocations": slate_allocations,
            "leftover_stats": leftover_stats,
        },
        None,
        None,
    )
    result = {
        "lineups": selected,
        "exposure_report": exposure_report,
        "slate_allocations": slate_allocations,
        "leftover_stats": leftover_stats,
    }
    if as_plan:
        plan = submit_plan_tool.submit_plan(
            slates[0]["id"] if slates else "",
            selected,
            bankroll or 0.0,
            unit_fraction or 0.02,
            entry_fee or 0.0,
            max_entries or 0,
            seed,
        )
        result["plan"] = plan
        savepoint_log("post_portfolio_plan", plan, None, bankroll)
    return result
