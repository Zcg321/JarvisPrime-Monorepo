from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

from .adapters import base, results_dkcsv  # register


def ingest(path: str, ema_alpha: float = 0.35) -> Dict[str, Any]:
    rows = base.get("results:dkcsv").load(path)
    if not rows:
        raise ValueError("no rows")
    slate_id = rows[0]["slate_id"]
    agg: Dict[str, Dict[str, float]] = {}
    for r in rows:
        pid = r["player_id"]
        info = agg.setdefault(pid, {"payout": 0.0, "entries": 0})
        info["payout"] += float(r["payout"])
        info["entries"] += 1
    report = {"slate_id": slate_id, "players": agg}
    reports_dir = Path("logs/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"results_{slate_id}.json"
    report_path.write_text(json.dumps(report, indent=2))
    roi_path = Path("logs/ghosts/roi.jsonl")
    roi_path.parent.mkdir(parents=True, exist_ok=True)
    existing: Dict[tuple, float] = {}
    if roi_path.exists():
        for line in roi_path.read_text().splitlines():
            try:
                obj = json.loads(line)
            except Exception:
                continue
            existing[(obj.get("player_id"), obj.get("slate_type"))] = obj.get("roi", 0.0)
    slate_type = "showdown" if "SD" in slate_id else "classic"
    with roi_path.open("a") as fh:
        for pid, info in sorted(agg.items()):
            prev = existing.get((pid, slate_type), 0.0)
            ema = prev * (1 - ema_alpha) + info["payout"] * ema_alpha
            fh.write(json.dumps({
                "ts": int(Path(path).stat().st_mtime),
                "player_id": pid,
                "slate_type": slate_type,
                "roi": round(ema, 6),
            }) + "\n")
    return {"report_path": str(report_path)}
