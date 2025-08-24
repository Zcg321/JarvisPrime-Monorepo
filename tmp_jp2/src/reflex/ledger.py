"""Daily bankroll ledger enforcing stop rules."""
from __future__ import annotations

import json
import datetime as dt
from pathlib import Path
from typing import Optional

from . import policy
LEDGER_DIR = Path("logs/ledger")
LEDGER_PATH = LEDGER_DIR / "daily_ledger.jsonl"  # legacy path


def _path(token_id: Optional[str] = None) -> Path:
    token = token_id or policy.current_token()
    return LEDGER_DIR / f"{token}.jsonl"


def record(
    amount: float,
    outcome: Optional[float] = None,
    ts: Optional[dt.datetime] = None,
    token_id: Optional[str] = None,
) -> None:
    path = _path(token_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = ts or dt.datetime.utcnow()
    rec = {"ts": ts.isoformat(), "amount": float(amount)}
    if outcome is not None:
        rec["outcome"] = float(outcome)
    with path.open("a") as f:
        f.write(json.dumps(rec) + "\n")


def day_pnl(day: Optional[dt.date] = None, token_id: Optional[str] = None) -> float:
    day = day or dt.datetime.utcnow().date()
    path = _path(token_id)
    if not path.exists():
        return 0.0
    total = 0.0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        try:
            if dt.datetime.fromisoformat(rec["ts"]).date() != day:
                continue
        except Exception:
            continue
        if rec.get("outcome") is None:
            continue
        total += float(rec.get("outcome", 0)) - float(rec.get("amount", 0))
    return total
