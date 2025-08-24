"""Daily bankroll ledger enforcing stop rules."""
from __future__ import annotations

import json
import datetime as dt
from pathlib import Path
from typing import Optional

LEDGER_PATH = Path("logs/ledger/daily_ledger.jsonl")


def record(amount: float, outcome: Optional[float] = None, ts: Optional[dt.datetime] = None) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = ts or dt.datetime.utcnow()
    rec = {"ts": ts.isoformat(), "amount": float(amount)}
    if outcome is not None:
        rec["outcome"] = float(outcome)
    with LEDGER_PATH.open("a") as f:
        f.write(json.dumps(rec) + "\n")


def day_pnl(day: Optional[dt.date] = None) -> float:
    day = day or dt.datetime.utcnow().date()
    if not LEDGER_PATH.exists():
        return 0.0
    total = 0.0
    for line in LEDGER_PATH.read_text().splitlines():
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
