from __future__ import annotations

"""Per-token risk policy utilities."""

import hashlib
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Dict, Set

import yaml

POLICY_FILE = Path("configs/risk.yaml")
_TOKEN: ContextVar[str] = ContextVar("token_id", default="anon")
_TOOL: ContextVar[str] = ContextVar("tool", default="")
_CACHE: Dict[str, Any] | None = None
_VERSION: str | None = None
DRY_RUN_TOOLS: Set[str] = {
    "submit_sim",
    "submit_plan",
    "portfolio_dedupe",
    "late_swap",
    "portfolio_export",
    "roi_attrib",
    "portfolio_ab",
}


def set_token(token_id: str) -> None:
    _TOKEN.set(token_id or "anon")


def set_tool(tool: str) -> None:
    _TOOL.set(tool or "")


def current_tool() -> str:
    return _TOOL.get()


def current_token() -> str:
    return _TOKEN.get()


def _load() -> Dict[str, Any]:
    global _CACHE, _VERSION
    try:
        data = yaml.safe_load(POLICY_FILE.read_text()) or {}
    except Exception:
        data = {}
    _CACHE = data
    try:
        _VERSION = hashlib.sha256(POLICY_FILE.read_bytes()).hexdigest()[:8]
    except Exception:
        _VERSION = ""
    return data


def policy_version() -> str:
    if _VERSION is None:
        _load()
    return _VERSION or ""


def get_policy(token_id: str) -> Dict[str, Any]:
    data = _CACHE or _load()
    base = {k: v for k, v in data.items() if k != "policies"}
    for p in data.get("policies", []) or []:
        if p.get("token_id") == token_id:
            merged = base.copy()
            merged.update(p)
            merged["_explicit"] = True
            return merged
    base["_explicit"] = False
    return base


class RiskViolation(Exception):
    """Raised when a risk policy blocks an action."""

    pass


def unit_size(token_id: str | None = None) -> float:
    """Compute deterministic unit size for a token.

    The size is ``bankroll * unit_fraction`` clamped between ``min_unit`` and
    ``max_unit`` as defined in the merged policy. No Kelly blending is
    implemented in this lightweight version.
    """

    pol = get_policy(token_id or current_token())
    bankroll = float(pol.get("bankroll", 0.0))
    uf = float(pol.get("unit_fraction", 0.0))
    unit = bankroll * uf
    unit = max(float(pol.get("min_unit", 0.0)), unit)
    unit = min(float(pol.get("max_unit", unit)), unit)
    return unit
