"""Deterministic lineup beam search (simplified)."""

from __future__ import annotations

import random
from typing import Dict, Any, List

from src.savepoint.logger import savepoint_log


def lineup_agent(
    seed_lineup: Dict[str, Any],
    beam: int = 8,
    depth: int = 4,
    constraints: Dict[str, Any] | None = None,
    weights: Dict[str, float] | None = None,
    seed: int = 0,
) -> Dict[str, Any]:
    random.seed(seed)
    trail: List[Dict[str, Any]] = [seed_lineup]
    result = {"best_lineup": seed_lineup, "beam_trail": trail, "leftover": 0}
    savepoint_log("post_lineup_agent", {"best_lineup": seed_lineup})
    return result


def lineup_agent_diverse(
    seed_lineup: Dict[str, Any],
    beam: int = 8,
    depth: int = 4,
    constraints: Dict[str, Any] | None = None,
    weights: Dict[str, float] | None = None,
    metric: str = "jaccard",
    seed: int = 0,
) -> Dict[str, Any]:
    """Stub diversity-aware beam search.

    For this simplified implementation we reuse :func:`lineup_agent` to
    obtain a deterministic best lineup and then compute a diversity metric
    against the single-member frontier. This mirrors the interface of a
    full diversity-constrained beam explorer while remaining lightweight
    for tests.
    """

    base = lineup_agent(
        seed_lineup=seed_lineup,
        beam=beam,
        depth=depth,
        constraints=constraints,
        weights=weights,
        seed=seed,
    )

    from .portfolio_diversity import portfolio_diversity

    summary = portfolio_diversity(
        [base["best_lineup"]],
        weights or {},
        metric=metric,
        seed=seed,
    )["summary"].get(metric, 0.0)

    result = {
        "best_lineup": base["best_lineup"],
        "beam_trail": base["beam_trail"],
        "leftover": base.get("leftover", 0),
        "diversity_metric": summary,
    }
    savepoint_log("post_lineup_agent_diverse", {"best_lineup": base["best_lineup"]})
    return result
