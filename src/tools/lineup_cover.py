from __future__ import annotations

import random
from typing import Any, Dict, List

from src.savepoint import logger as savepoint_logger


def minimize(
    lineups: List[Dict[str, Any]],
    targets: Dict[str, Dict[str, float]],
    min_set: bool = True,
    seed: int = 1337,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    selected: List[Dict[str, Any]] = []
    remaining = list(lineups)
    epsilon = 0.02

    def coverage_ok() -> bool:
        n = len(selected)
        if not n:
            return False
        for pid, tgt in targets.get("players", {}).items():
            count = sum(pid in [p.get("player_id") for p in lu.get("players", [])] for lu in selected)
            if count / n + epsilon < tgt:
                return False
        for team, tgt in targets.get("teams", {}).items():
            count = sum(team in [p.get("team") for p in lu.get("players", [])] for lu in selected)
            if count / n + epsilon < tgt:
                return False
        return True

    while remaining and (not coverage_ok() or not min_set):
        remaining.sort(key=lambda l: (-l.get("leverage", 0), -l.get("roi", 0), l.get("id", "")))
        pick = remaining.pop(0)
        selected.append(pick)
        if min_set and coverage_ok():
            break

    selected_ids = [l.get("id") for l in selected]
    cov_players = {}
    n = len(selected)
    for pid in targets.get("players", {}):
        cov_players[pid] = sum(
            pid in [p.get("player_id") for p in l.get("players", [])] for l in selected
        ) / n if n else 0.0
    cov_teams = {}
    for tm in targets.get("teams", {}):
        cov_teams[tm] = sum(
            tm in [p.get("team") for p in l.get("players", [])] for l in selected
        ) / n if n else 0.0
    savepoint_logger.savepoint_log("post_lineup_cover", {"selected": selected_ids}, None, None)
    return {"selected_ids": selected_ids, "coverage": {"players": cov_players, "teams": cov_teams}, "leftover": len(lineups) - n}
