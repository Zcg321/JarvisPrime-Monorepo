"""Minimal correlation helpers for showdown stacking."""
from __future__ import annotations

from typing import List, Dict, Any


def bias_players(players: List[Dict[str, Any]], cpt_team: str, bringback: bool) -> None:
    """Apply in-place projection bonuses for stacking heuristics.

    Players on the captain team receive a small boost. If ``bringback`` is
    true, opponents receive a smaller boost to encourage at least one.
    """
    for p in players:
        team = p.get("team")
        if team == cpt_team:
            p["proj"] = float(p.get("proj", 0.0)) * 1.05
        elif bringback:
            p["proj"] = float(p.get("proj", 0.0)) * 1.02
