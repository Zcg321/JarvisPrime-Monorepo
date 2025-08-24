from __future__ import annotations
import csv
import os
import time
import threading
from pathlib import Path
from typing import List, Dict, Any

from .base import DataAdapter, register

class OwnershipDKCSV(DataAdapter):
    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def load(self, path: str | Path) -> List[Dict[str, Any]]:
        p = Path(path)
        with self._lock:
            self._ttl = int(os.environ.get("OWNERSHIP_TTL_S", "300"))
            mtime = p.stat().st_mtime
            now = time.time()
            cached = self._cache.get(str(p))
            if cached and cached["mtime"] == mtime and now - cached["ts"] <= self._ttl:
                return cached["data"]
            with p.open(newline="") as fh:
                reader = csv.DictReader(fh)
                required = {"player_id", "team", "proj_points", "field_own_pct"}
                fields = set(reader.fieldnames or [])
                if not required.issubset(fields):
                    missing = required - fields
                    raise ValueError(f"missing columns: {sorted(missing)}")
                rows: List[Dict[str, Any]] = []
                for row in reader:
                    rows.append({
                        "player_id": row["player_id"],
                        "team": row["team"],
                        "proj_points": float(row["proj_points"]),
                        "field_own_pct": float(row["field_own_pct"]),
                    })
            self._cache[str(p)] = {"mtime": mtime, "data": rows, "ts": now}
            return rows

register("ownership:dkcsv", OwnershipDKCSV())
