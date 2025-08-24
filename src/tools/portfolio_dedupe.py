from __future__ import annotations

import random
from typing import Any, Dict, List

from src.savepoint.logger import savepoint_log


def portfolio_dedupe(
    lineups: List[Dict[str, Any]],
    max_dupe: int = 1,
    min_hamming: int = 2,
    tie_break: Dict[str, float] | None = None,
    seed: int = 1337,
) -> Dict[str, Any]:
    """Remove near-duplicate lineups deterministically."""
    rng = random.Random(seed)
    tie_break = tie_break or {}
    w_roi = tie_break.get("roi", 1.0)
    w_lev = tie_break.get("lev", tie_break.get("leverage", 0.0))
    w_ent = tie_break.get("entropy", 0.0)

    def score(lu: Dict[str, Any]) -> float:
        return w_roi * lu.get("roi", 0.0) + w_lev * lu.get("leverage", 0.0) + w_ent * lu.get("entropy", 0.0) + rng.random() * 1e-9

    def hamming(a: Dict[str, Any], b: Dict[str, Any]) -> int:
        pa = [p.get("player_id") for p in a.get("players", [])]
        pb = [p.get("player_id") for p in b.get("players", [])]
        n = max(len(pa), len(pb))
        pa += [""] * (n - len(pa))
        pb += [""] * (n - len(pb))
        return sum(1 for x, y in zip(pa, pb) if x != y)

    dup_counts: Dict[tuple, int] = {}
    kept: List[Dict[str, Any]] = []
    dropped: List[str] = []

    for lu in sorted(lineups, key=lambda x: (-score(x), x.get("id", ""))):
        key = tuple(sorted(p.get("player_id") for p in lu.get("players", [])))
        if dup_counts.get(key, 0) >= max_dupe:
            dropped.append(lu.get("id"))
            continue
        if any(hamming(lu, k) < min_hamming for k in kept):
            dropped.append(lu.get("id"))
            continue
        kept.append(lu)
        dup_counts[key] = dup_counts.get(key, 0) + 1

    kept_ids = [k.get("id") for k in kept]
    pairs = len(kept) * (len(kept) - 1) // 2
    total_ham = 0
    for i in range(len(kept)):
        for j in range(i + 1, len(kept)):
            total_ham += hamming(kept[i], kept[j])
    avg_ham = total_ham / pairs if pairs else 0.0
    savepoint_log("post_portfolio_dedupe", {"kept": kept_ids})
    return {
        "kept_ids": kept_ids,
        "dropped_ids": dropped,
        "stats": {"dup_removed": len(dropped), "avg_hamming": avg_ham},
    }
