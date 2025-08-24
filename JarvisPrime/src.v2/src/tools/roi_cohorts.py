"""ROI cohort analytics."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any

from src.serve import alerts

LOG_PATH = Path(os.environ.get("ROI_LOG_DIR_LEGACY", "logs/ghosts")) / "roi_daily.jsonl"


def roi_cohorts(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    lookback_days = int(args.get("lookback_days", 90))
    group_by = args.get("group_by") or ["slate_type"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    if not LOG_PATH.exists():
        return []
    groups: Dict[tuple, List[float]] = {}
    with LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            ts = datetime.fromtimestamp(rec.get("ts", 0), tz=timezone.utc)
            if ts < cutoff:
                continue
            key = tuple(rec.get(g) for g in group_by)
            groups.setdefault(key, []).append(float(rec.get("roi", 0.0)))
    out = []
    alpha = 0.35
    for key, values in groups.items():
        values.sort()
        n = len(values)
        mean = sum(values) / n
        ema = None
        for v in values:
            ema = v if ema is None else alpha * v + (1 - alpha) * ema
        p25 = values[int(0.25 * (n - 1))]
        p50 = values[int(0.5 * (n - 1))]
        p75 = values[int(0.75 * (n - 1))]
        cohort = {group_by[i]: key[i] for i in range(len(group_by))}
        out.append(
            {
                "cohort": cohort,
                "count": n,
                "mean_roi": mean,
                "ema_roi": ema,
                "p25": p25,
                "p50": p50,
                "p75": p75,
            }
        )
    out.sort(key=lambda x: tuple(str(x["cohort"].get(g, "")) for g in group_by))
    return out


def detect_drift(tau: float = 0.05) -> List[Dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    recs = []
    with LOG_PATH.open() as f:
        for line in f:
            if not line.strip():
                continue
            recs.append(json.loads(line))
    if not recs:
        return []
    latest = max(r.get("ts", 0) for r in recs)
    end = datetime.fromtimestamp(latest, tz=timezone.utc)
    start_last = end - timedelta(days=7)
    start_prev = start_last - timedelta(days=7)
    cohorts: Dict[tuple, Dict[str, List[float]]] = {}
    for rec in recs:
        ts = datetime.fromtimestamp(rec.get("ts", 0), tz=timezone.utc)
        if ts < start_prev:
            continue
        key = (rec.get("slate_type"), rec.get("position_bucket"))
        which = "last" if ts >= start_last else "prev"
        cohorts.setdefault(key, {"last": [], "prev": []})[which].append(float(rec.get("roi", 0.0)))
    drifts = []
    alerted = set()
    for key, vals in cohorts.items():
        last, prev = vals["last"], vals["prev"]
        if not last or not prev:
            continue
        mean_last = sum(last) / len(last)
        mean_prev = sum(prev) / len(prev)
        if abs(mean_last - mean_prev) > tau:
            cohort = {"slate_type": key[0], "position_bucket": key[1]}
            drifts.append({"cohort": cohort, "delta_mean": mean_last - mean_prev})
            ckey = json.dumps(cohort)
            if ckey not in alerted:
                alerts.log_event("cohort_drift", ckey, severity="WARN")
                alerted.add(ckey)
    return drifts
