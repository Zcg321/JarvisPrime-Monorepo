"""Heuristic exposure solver for DFS lineups."""

import random
from typing import Dict, Any, List, Optional

from . import ghost_dfs


def solve(
    slate_id: str,
    n_lineups: int,
    max_from_team: int = 3,
    global_exposure_caps: Optional[Dict[str, float]] = None,
    seed: int = 0,
) -> Dict[str, Any]:
    """Return a lineup set respecting exposure caps and team limits."""

    caps = global_exposure_caps or {}
    pool = ghost_dfs.seed_pool(slate_id, seed, pool_size=max(n_lineups * 3, 1))
    selected: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    rng = random.Random(f"{slate_id}:{seed}")
    for item in pool:
        if len(selected) >= n_lineups:
            break
        lineup = item["players"]
        # team counts per lineup
        teams: Dict[str, int] = {}
        players: List[str] = []
        for p in lineup:
            pid = p.get("player") or p.get("name") or ""
            team = p.get("team") or f"T{hash(pid) % 10}"
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
        for pid in players:
            counts[pid] = counts.get(pid, 0) + 1
    report = {pid: counts.get(pid, 0) / len(selected) if selected else 0.0 for pid in caps}
    return {"lineups": selected, "exposure": report}
