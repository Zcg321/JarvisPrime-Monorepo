from __future__ import annotations

import random
from typing import Any, Dict, List

from src.savepoint.logger import savepoint_log


def portfolio_diversity(
    lineups: List[Dict[str, Any]],
    weights: Dict[str, float] | None = None,
    metric: str = "jaccard",
    exposure_caps: Dict[str, float] | None = None,
    seed: int = 1337,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    weights = weights or {}
    w_roi = weights.get("roi", 0.0)
    w_lev = weights.get("leverage", 0.0)
    w_div = weights.get("diversity", 0.0)
    remaining = list(lineups)
    selected: List[Dict[str, Any]] = []
    exposure_caps = exposure_caps or {}

    def diversity_gain(lu: Dict[str, Any]) -> float:
        if not selected:
            return 1.0
        players = set(p.get("player_id") for p in lu.get("players", []))
        if metric == "entropy":
            counts: Dict[str, int] = {}
            for s in selected:
                for p in s.get("players", []):
                    pid = p.get("player_id")
                    counts[pid] = counts.get(pid, 0) + 1
            ent = 0.0
            total = len(selected)
            for c in counts.values():
                prob = c / total
                ent -= prob * (prob and __import__("math").log(prob, 2))
            base = len(counts) or 1
            new_counts = counts.copy()
            for p in players:
                new_counts[p] = new_counts.get(p, 0) + 1
            ent2 = 0.0
            total2 = total + 1
            for c in new_counts.values():
                prob = c / total2
                ent2 -= prob * (prob and __import__("math").log(prob, 2))
            return ent2 - ent
        else:
            d = 0.0
            for s in selected:
                other = set(p.get("player_id") for p in s.get("players", []))
                inter = len(players & other)
                union = len(players | other) or 1
                d += 1 - inter / union
            return d / len(selected)

    while remaining:
        best = None
        best_score = -1e9
        look = sorted(remaining, key=lambda x: x.get("id", ""))[:8]
        for lu in look:
            if exposure_caps:
                valid = True
                for pid, cap in exposure_caps.items():
                    count = sum(pid in [p.get("player_id") for p in s.get("players", [])] for s in selected)
                    if pid in [p.get("player_id") for p in lu.get("players", [])] and (count + 1) / (len(selected) + 1) > cap:
                        valid = False
                        break
                if not valid:
                    continue
            score = (
                w_roi * lu.get("roi", 0.0)
                + w_lev * lu.get("leverage", 0.0)
                + w_div * diversity_gain(lu)
                + rng.random() * 1e-9
            )
            if score > best_score or (
                score == best_score and lu.get("id", "") < best.get("id", "")
            ):
                best_score, best = score, lu
        if best is None:
            break
        selected.append(best)
        remaining.remove(best)

    sel_ids = [s.get("id") for s in selected]
    jacc = 0.0
    pairs = 0
    for i in range(len(selected)):
        for j in range(i + 1, len(selected)):
            a = set(p.get("player_id") for p in selected[i].get("players", []))
            b = set(p.get("player_id") for p in selected[j].get("players", []))
            inter = len(a & b)
            union = len(a | b) or 1
            jacc += 1 - inter / union
            pairs += 1
    jacc = jacc / pairs if pairs else 0.0
    counts: Dict[str, int] = {}
    for s in selected:
        for p in s.get("players", []):
            pid = p.get("player_id")
            counts[pid] = counts.get(pid, 0) + 1
    ent = 0.0
    total = len(selected) or 1
    for c in counts.values():
        prob = c / total
        ent -= prob * (prob and __import__("math").log(prob, 2))
    summary = {"entropy": ent, "jaccard": jacc}
    savepoint_log("post_portfolio_diversity", {"selected": sel_ids})
    scores = []
    for s in selected:
        scores.append(
            {
                "id": s.get("id"),
                "roi": s.get("roi"),
                "leverage": s.get("leverage"),
            }
        )
    return {"selected": sel_ids, "scores": scores, "summary": summary}
