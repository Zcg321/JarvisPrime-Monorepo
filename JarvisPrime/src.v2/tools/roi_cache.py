"""Simple ROI EMA cache with mtime/TTL invalidation."""
from __future__ import annotations

import time
from typing import Any, Dict
from pathlib import Path

_CACHE: Dict[str, Any] | None = None
_MTIME: float = 0.0
_TS: float = 0.0
TTL = 300.0


def load_ema(lookback_days: int, alpha: float, multi: bool = False):
    global _CACHE, _MTIME, _TS
    from . import dfs as _dfs
    path = _dfs.ROI_LOG
    mtime = path.stat().st_mtime if path.exists() else 0.0
    now = time.time()
    key = (multi, lookback_days, alpha)
    if _CACHE and _CACHE.get("key") == key and now - _TS < TTL and mtime == _MTIME:
        return _CACHE["data"]
    data = (
        _dfs._load_roi_multi_ema(lookback_days, alpha)
        if multi
        else _dfs._load_roi_ema(lookback_days, alpha)
    )
    _CACHE = {"key": key, "data": data}
    _MTIME = mtime
    _TS = now
    return data


def _invalidate():
    global _CACHE
    _CACHE = None
