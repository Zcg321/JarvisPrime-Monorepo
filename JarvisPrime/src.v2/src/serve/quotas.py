import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from src.core.logio import append_jsonl_rotating

USAGE_PATH = Path("logs/usage/usage_daily.jsonl")
USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _iter(date: str):
    if not USAGE_PATH.exists():
        return
    with USAGE_PATH.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("date") == date:
                yield rec


def usage(date: str | None = None) -> Dict[str, Dict[str, int]]:
    date = date or _today()
    totals: Dict[str, Dict[str, int]] = {}
    for rec in _iter(date):
        token = rec.get("token_id")
        if not token:
            continue
        if rec.get("reset"):
            totals[token] = {"requests": 0, "cpu_ms": 0}
            continue
        t = totals.setdefault(token, {"requests": 0, "cpu_ms": 0})
        t["requests"] += int(rec.get("requests", 0))
        t["cpu_ms"] += int(rec.get("cpu_ms", 0))
    return totals


def _quota_for(token_id: str, cfg: Dict[str, Any]) -> Dict[str, int]:
    overrides = cfg.get("overrides", {})
    if token_id in overrides:
        return overrides[token_id]
    return cfg.get("default", {})


def allow(token_id: str, cfg: Dict[str, Any]) -> bool:
    q = _quota_for(token_id, cfg)
    today = usage(_today()).get(token_id, {"requests": 0})
    if today["requests"] >= q.get("requests", float("inf")):
        return False
    append_jsonl_rotating(str(USAGE_PATH), {
        "date": _today(),
        "token_id": token_id,
        "requests": 1,
        "cpu_ms": 0,
    })
    return True


def add_cpu(token_id: str, cpu_ms: int) -> None:
    append_jsonl_rotating(str(USAGE_PATH), {
        "date": _today(),
        "token_id": token_id,
        "requests": 0,
        "cpu_ms": int(cpu_ms),
    })


def reset(token_id: str, date: str | None = None) -> None:
    append_jsonl_rotating(str(USAGE_PATH), {
        "date": date or _today(),
        "token_id": token_id,
        "reset": True,
    })
