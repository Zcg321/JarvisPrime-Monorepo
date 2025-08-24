"""Slate schedule loader and query utilities."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Dict, Any

REQUIRED = {"date", "slate_id", "type", "teams"}


def _load_file(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if p.suffix == ".json":
        rows = json.loads(p.read_text())
    else:
        with p.open(newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
    out: List[Dict[str, Any]] = []
    for r in rows:
        if not REQUIRED.issubset(r):
            missing = REQUIRED - set(r)
            raise ValueError(f"missing fields: {sorted(missing)}")
        teams = r["teams"]
        if isinstance(teams, str):
            teams = [t for t in teams.replace(";", "@").replace(",", "@").split("@") if t]
        out.append({
            "date": r["date"],
            "slate_id": r["slate_id"],
            "type": r["type"],
            "teams": teams,
        })
    return out


def query(start: str, end: str, type: str | None = None, path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Query schedules between dates inclusive."""
    if path is None:
        path = Path("data/schedule/samples/2025-10-25.json")
    rows = _load_file(path)
    res = [r for r in rows if start <= r["date"] <= end]
    if type:
        res = [r for r in res if r["type"] == type]
    res.sort(key=lambda r: r["slate_id"])
    return res
