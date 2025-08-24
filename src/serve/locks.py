from __future__ import annotations

from typing import List, Dict

from src.data import schedule


def get_locks(date: str, site: str) -> List[Dict[str, str]]:
    rows = schedule.query(date, date)
    out = []
    for r in rows:
        lock = f"{r['date']}T00:00:00Z"
        out.append({"slate_id": r["slate_id"], "lock_time": lock})
    return out
