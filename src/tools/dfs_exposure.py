"""Exposure balancing for DFS lineup pools.

MIT License (c) 2025 Zack
"""
from collections import defaultdict
from typing import Dict, List


def solve(pool: List[List[str]], constraints: Dict[str, Dict[str, float]]):
    """Select lineups respecting max exposure per player.

    Parameters
    ----------
    pool: list of lineups (each lineup is list of player names)
    constraints: dict of player -> {"max": float between 0 and 1}
    """
    selected: List[List[str]] = []
    counts = defaultdict(int)
    total = 0
    for lineup in pool:
        ok = True
        for name in lineup:
            lim = constraints.get(name, {}).get("max")
            if lim is not None and (counts[name] + 1) / (total + 1) > lim:
                ok = False
                break
        if ok:
            selected.append(lineup)
            total += 1
            for name in lineup:
                counts[name] += 1
    return selected
