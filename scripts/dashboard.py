import json
from pathlib import Path
import sys
import tarfile
import hashlib
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.serve import metrics, alerts
from src.tools import roi_cohorts
from datetime import datetime, timezone, timedelta


def _rolling_counts() -> dict:
    today = datetime.utcnow().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    alerts_counts = {d: 0 for d in days}
    if alerts.ALERT_PATH.exists():
        for ln in alerts.ALERT_PATH.open():
            try:
                rec = json.loads(ln)
            except Exception:
                continue
            d = datetime.fromtimestamp(rec.get("ts", 0), tz=timezone.utc).date()
            if d in alerts_counts:
                alerts_counts[d] += 1
    audit_counts = {d: 0 for d in days}
    for p in Path("logs/audit").glob("*.jsonl"):
        d = datetime.utcfromtimestamp(p.stat().st_mtime).date()
        if d in audit_counts:
            audit_counts[d] += 1
    sp_counts = {d: 0 for d in days}
    for p in Path("logs/savepoints").glob("*.json"):
        d = datetime.utcfromtimestamp(p.stat().st_mtime).date()
        if d in sp_counts:
            sp_counts[d] += 1
    return {
        "alerts": [alerts_counts[d] for d in days],
        "audit": [audit_counts[d] for d in days],
        "savepoints": [sp_counts[d] for d in days],
    }


def _drilldowns() -> dict:
    alerts_dd = alerts.get_last(20)
    audit_events = []
    for p in sorted(Path("logs/audit").glob("*.jsonl")):
        with p.open() as f:
            for ln in f:
                try:
                    audit_events.append(json.loads(ln))
                except Exception:
                    continue
    audit_dd = audit_events[-20:]
    sp_events = []
    for p in sorted(Path("logs/savepoints").glob("*.json")):
        try:
            sp_events.append(json.loads(p.read_text()))
        except Exception:
            continue
    sp_dd = sp_events[-20:]
    return {"alerts": alerts_dd, "audit": audit_dd, "savepoints": sp_dd}


def _spark(vals):
    if not vals:
        return ""
    width, height = 100, 20
    maxv = max(vals) or 1
    step = width / (len(vals) - 1 or 1)
    pts = [f"{i*step},{height - (v/maxv)*height}" for i, v in enumerate(vals)]
    d = "M" + " L".join(pts)
    return f'<svg width="{width}" height="{height}"><path d="{d}" fill="none" stroke="blue"/></svg>'

OUT = Path("artifacts/reports")


def main() -> None:
    health = {"status": "ok"}
    metrics_snap = metrics.METRICS.snapshot()
    alerts_data = alerts.get_last()
    audit_summary = {"files": len(list(Path("logs/audit").glob("*.jsonl")))}
    lineage_summary = {"savepoints": len(list(Path("logs/savepoints").glob("*.json")))}
    trends = _rolling_counts()
    drill = _drilldowns()
    drifts = roi_cohorts.detect_drift()
    data = {
        "health": health,
        "metrics": metrics_snap,
        "alerts": alerts_data,
        "audit": audit_summary,
        "lineage": lineage_summary,
        "trends": trends,
        "drilldown": drill,
        "cohort_drift_active": len(drifts),
        "cohort_drift": drifts,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "dashboard.json").write_text(json.dumps(data))
    badge = " ✦" + str(len(drifts)) if drifts else ""
    html = [f"<html><body><h1>Dashboard{badge}</h1>"]
    if drifts:
        html.append(f"<h2>Cohort Drift</h2><pre>{json.dumps(drifts)}</pre>")
    for section in ["health", "metrics", "alerts", "audit", "lineage"]:
        html.append(f"<h2>{section.title()}</h2><pre>{json.dumps(data[section])}</pre>")
    html.append("<h2>Trends</h2>")
    for k, vals in trends.items():
        html.append(
            f"<h3>{k}</h3><details><summary>{_spark(vals)}</summary><pre>{json.dumps(drill[k])}</pre></details>"
        )
    html.append(
        "<script>setInterval(async()=>{await fetch('/dashboard/json');},60000)</script></body></html>"
    )
    (OUT / "dashboard.html").write_text("".join(html))
    sparks = {k: _spark(v) for k, v in trends.items()}
    (OUT / "sparklines.svg").write_text("\n".join(sparks.values()))
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    tar_path = OUT / f"dashboard_{ts}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for name in ["dashboard.json", "dashboard.html", "sparklines.svg"]:
            tar.add(OUT / name, arcname=name)
    sha = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    (OUT / "SHA256SUMS").write_text(f"{sha}  {tar_path.name}\n")

if __name__ == "__main__":
    main()
