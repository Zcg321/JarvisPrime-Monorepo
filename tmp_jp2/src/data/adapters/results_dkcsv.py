from __future__ import annotations
import csv
import json
import time
from pathlib import Path
from typing import Dict, Any, List

from .base import DataAdapter, register

class ResultsDKCSV(DataAdapter):
    def load(self, path: str) -> List[Dict[str, Any]]:
        p = Path(path)
        rows: List[Dict[str, Any]] = []
        with p.open() as f:
            reader = csv.DictReader(f)
            required = {"contest_id", "slate_id", "lineup_id", "player_id", "fpts", "rank", "payout"}
            if not required.issubset(reader.fieldnames or []):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"missing columns: {sorted(missing)}")
            for row in reader:
                rows.append(row)
        return rows

register("results:dkcsv", ResultsDKCSV())
