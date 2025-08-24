from __future__ import annotations

import random
from typing import Any, Dict, List

from src.savepoint.logger import savepoint_log


def late_swap(
    lineup: Dict[str, Any],
    news: List[Dict[str, Any]],
    remaining_games: List[Dict[str, Any]],
    constraints: Dict[str, Any] | None = None,
    seed: int = 1337,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    constraints = constraints or {}
    cap = constraints.get("salary_cap", 50000)
    max_team = constraints.get("max_from_team", 3)
    pool: List[Dict[str, Any]] = []
    for g in remaining_games:
        pool.extend(g.get("players", []))
    lineup_players = [p.copy() for p in lineup.get("players", [])]
    changes: List[Dict[str, str]] = []
    for item in news:
        if item.get("status") != "out":
            continue
        pid = item.get("player_id")
        idx = next((i for i, p in enumerate(lineup_players) if p.get("player_id") == pid), None)
        if idx is None:
            continue
        pos = lineup_players[idx].get("position")
        current_ids = {p.get("player_id") for p in lineup_players}
        team_counts: Dict[str, int] = {}
        for p in lineup_players:
            team = p.get("team")
            team_counts[team] = team_counts.get(team, 0) + 1
        team_counts[lineup_players[idx].get("team")] -= 1
        best = None
        best_score = -1e9
        for cand in pool:
            if cand.get("player_id") in current_ids:
                continue
            if cand.get("position") != pos:
                continue
            if team_counts.get(cand.get("team"), 0) + 1 > max_team:
                continue
            new_salary = sum(p.get("salary", 0) for p in lineup_players) - lineup_players[idx].get("salary", 0) + cand.get("salary", 0)
            if new_salary > cap:
                continue
            score = cand.get("roi", 0.0) + cand.get("leverage", 0.0) + rng.random() * 1e-9
            if score > best_score or (score == best_score and cand.get("player_id") < best.get("player_id", "")):
                best = cand
                best_score = score
        if best:
            out_id = lineup_players[idx].get("player_id")
            lineup_players[idx] = best.copy()
            changes.append({"out": out_id, "in": best.get("player_id")})
    total_salary = sum(p.get("salary", 0) for p in lineup_players)
    if total_salary > cap:
        raise ValueError("salary_cap_exceeded")
    savepoint_log("post_late_swap", {"changes": changes})
    return {"swapped_lineup": {"players": lineup_players}, "changes": changes}
