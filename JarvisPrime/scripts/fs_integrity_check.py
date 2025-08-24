"""Filesystem integrity check."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any

DIRS = [
    "logs/savepoints",
    "logs/ghosts",
    "logs/ledger",
    "logs/perf",
    "logs/reports",
    "data/ownership",
]


def run() -> Dict[str, Any]:
    summary = {"missing": [], "tmp_cleaned": 0}
    for d in DIRS:
        p = Path(d)
        if not p.exists():
            summary["missing"].append(d)
            continue
        for tmp in p.rglob("*.tmp"):
            tmp.unlink(missing_ok=True)
            summary["tmp_cleaned"] += 1
        for json_file in p.rglob("*.json"):
            try:
                json.loads(json_file.read_text())
            except Exception:
                summary.setdefault("invalid", []).append(str(json_file))
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
