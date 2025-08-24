"""Council scoring adjustments for DFS lineups."""
from __future__ import annotations

from typing import Dict, Any
from pathlib import Path
import os
import yaml

CONFIG = Path(os.environ.get("COUNCIL_CONFIG", "configs/council.yaml"))
try:
    _CFG: Dict[str, Dict[str, float]] = yaml.safe_load(CONFIG.read_text()) or {}
except Exception:
    _CFG = {}


def _bound(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def adjust_projection(proj: float, ownership: float | None, mode: str) -> float:
    """Return adjusted projection given ownership (0-1) and scoring mode."""
    if ownership is None:
        return proj
    lev = 1.0 - ownership
    if mode == "goku":
        w = _bound(_CFG.get("goku", {}).get("leverage", 0.5), 0.0, 1.0)
        return proj * (1 + w * lev)
    if mode == "vegeta":
        base = _bound(_CFG.get("vegeta", {}).get("base", 0.5), 0.0, 1.0)
        lev_w = _bound(_CFG.get("vegeta", {}).get("leverage", 1.0), 0.0, 2.0)
        return proj * (base + lev_w * lev)
    if mode == "piccolo":
        risk = _bound(_CFG.get("piccolo", {}).get("risk", 0.3), 0.0, 1.0)
        return proj * (1 - risk * ownership)
    w = _bound(_CFG.get("gohan", {}).get("leverage", 0.25), 0.0, 1.0)
    return proj * (1 + w * lev)
