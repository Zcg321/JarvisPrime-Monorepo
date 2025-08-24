from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from src.savepoint.logger import savepoint_log


def portfolio_export(
    slate_id: str,
    lineups: List[Dict[str, Any]],
    format: str = "dk_csv",
    seed: int = 0,
    overwrite: bool = False,
) -> Dict[str, Any]:
    if format != "dk_csv":
        raise ValueError("unsupported_format")
    out_dir = Path("artifacts/exports/dk")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{slate_id}.csv"
    if csv_path.exists() and not overwrite:
        raise ValueError("export_exists")
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["PG", "SG", "SF", "PF", "C", "G", "F", "UTIL"])
        for lu in lineups:
            row = [lu.get(pos, "") for pos in ["PG", "SG", "SF", "PF", "C", "G", "F", "UTIL"]]
            writer.writerow(row)
    sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    manifest = {"sha256": sha, "count": len(lineups), "slate_id": slate_id}
    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest))
    savepoint_log("post_portfolio_export", {"slate_id": slate_id})
    return {"path": str(csv_path), "manifest": manifest}
