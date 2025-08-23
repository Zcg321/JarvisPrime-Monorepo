import random
from typing import List, Dict, Optional


def dfs_sim(lineup: List[Dict], sims: int = 1000, seed: Optional[int] = None) -> Dict[str, float]:
    """Simulate DFS outcomes for a lineup.

    A local ``random.Random`` instance is optionally seeded for deterministic
    unit tests without affecting global state.
    """
    if not lineup:
        return {"mean": 0.0, "stdev": 0.0, "p95": 0.0}
    rng = random.Random(seed)
    totals = [
        sum(p.get("proj", 0) + rng.gauss(0, 1) for p in lineup)
        for _ in range(max(1, sims))
    ]
    totals.sort()
    n = len(totals)
    mean = sum(totals) / n
    stdev = (sum((x - mean) ** 2 for x in totals) / n) ** 0.5
    p95 = totals[int(0.95 * (n - 1))]
    return {"mean": mean, "stdev": stdev, "p95": p95}
