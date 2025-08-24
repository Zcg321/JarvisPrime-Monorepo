"""Simple deterministic portfolio optimizer.

Scores lineups based on ROI, leverage and exposure violation weights
and returns a reordered lineup list.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional


def optimize(
    lineups: List[Dict[str, Any]],
    objectives: Optional[Dict[str, float]] = None,
    seed: int = 0,
) -> List[Dict[str, Any]]:
    """Reorder lineups using a weighted score.

    Each lineup may contain optional keys: ``roi``, ``leverage`` and
    ``exposure_violation``. Missing keys default to ``0``. The score used is::

        base + w_roi * roi + w_lev * leverage - w_exp * exposure_violation

    where ``base`` preserves deterministic ordering when weights are ``0``.
    """
    if not objectives:
        return list(lineups)
    w_roi = float(objectives.get("roi_gain", 0.0))
    w_lev = float(objectives.get("leverage_gain", 0.0))
    w_exp = float(objectives.get("exposure_penalty", 0.0))
    if w_roi == 0 and w_lev == 0 and w_exp == 0:
        return list(lineups)
    scored = []
    for idx, ln in enumerate(lineups):
        roi = float(ln.get("roi", 0.0))
        lev = float(ln.get("leverage", 0.0))
        exp = float(ln.get("exposure_violation", 0.0))
        score = idx + w_roi * roi + w_lev * lev - w_exp * exp
        scored.append((score, idx, ln))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [ln for _, _, ln in scored]
