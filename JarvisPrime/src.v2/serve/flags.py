from __future__ import annotations

"""Runtime feature flags with canary percentage splits."""

import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from src.serve import alerts

FILE = Path("configs/flags.yaml")
try:
    _cfg = yaml.safe_load(FILE.read_text()) or {}
except Exception:
    _cfg = {}

_CANARY = set(_cfg.get("canary_tokens", []))
_FLAGS: Dict[str, Dict[str, Any]] = {}
for k, v in _cfg.items():
    if k == "canary_tokens":
        continue
    if isinstance(v, dict):
        _FLAGS[k] = {"state": v.get("state", "on"), "percent": int(v.get("percent", 0))}
    else:
        _FLAGS[k] = {"state": v}


def _hash(token_id: str, name: str) -> int:
    h = hashlib.sha256(f"{token_id}:{name}".encode()).hexdigest()
    return int(h[:8], 16) % 100


def _is_canary(name: str, token_id: str | None) -> bool:
    flag = _FLAGS.get(name, {"state": "on"})
    if flag.get("state") != "canary":
        return False
    if token_id in _CANARY:
        return True
    return _hash(token_id or "", name) < int(flag.get("percent", 0))


def reason(name: str, token_id: str | None, role: str | None) -> Optional[str]:
    flag = _FLAGS.get(name, {"state": "on"})
    state = flag.get("state", "on")
    if state == "off":
        return "flag_off"
    if state == "on":
        return None
    if state == "canary":
        if role == "admin" or _is_canary(name, token_id):
            return None
        return "not_canary"
    return None


def allowed(name: str, token_id: str | None, role: str | None) -> bool:
    return reason(name, token_id, role) is None


def slo_breach(name: str) -> None:
    flag = _FLAGS.get(name)
    if not flag or flag.get("state") != "canary":
        return
    pct = int(flag.get("percent", 0))
    if pct > 1:
        new_pct = max(1, pct // 2)
        flag["percent"] = new_pct
        _save()
        alerts.log_event("flag_throttle", f"{name} -> {new_pct}%")


def flip(name: str, state: Optional[str] = None, percent: Optional[int] = None) -> None:
    flag = _FLAGS.setdefault(name, {})
    if state in {"on", "off", "canary"}:
        flag["state"] = state
    if percent is not None and flag.get("state") == "canary":
        flag["percent"] = int(percent)
    _save()


def dump() -> Dict[str, Any]:
    out = {k: dict(v) for k, v in _FLAGS.items()}
    out["canary_tokens"] = list(_CANARY)
    return out


def _save() -> None:
    data = dump()
    FILE.write_text(yaml.safe_dump(data, sort_keys=True))
