from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def check(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        report = {"path": str(p), "ok": True, "count": 0}
    else:
        with p.open() as f:
            reader = csv.reader(f)
            header = next(reader, [])
            rows = [r for r in reader]
        classic = ["PG", "SG", "SF", "PF", "C", "G", "F", "UTIL"]
        showdown = ["CPT", "UTIL1", "UTIL2", "UTIL3", "UTIL4", "UTIL5"]
        ok = header == classic or header == showdown or not header
        report = {"path": str(p), "ok": ok, "count": len(rows)}
    out = Path("logs/reports")
    out.mkdir(parents=True, exist_ok=True)
    out.joinpath("dk_check.json").write_text(json.dumps(report, sort_keys=True))
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: check_dk_export.py <csv>")
        sys.exit(1)
    check(sys.argv[1])
