import json
import os
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

BASE = Path(os.environ.get("METRICS_DIR", "logs/metrics"))
REQUESTS_LOG = BASE / "requests.jsonl"
ROLLUP_LOG = BASE / "rollup_hourly.jsonl"
BASE.mkdir(parents=True, exist_ok=True)


def _percentile(seq: List[float], pct: float) -> float:
    if not seq:
        return 0.0
    arr = sorted(seq)
    k = max(int(math.ceil(pct * len(arr))) - 1, 0)
    return arr[k]


def log_request(ts: float, tool: str, runtime: str, latency_ms: float, status: str, reason: str = "") -> None:
    rec = {
        "ts_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        "tool": tool,
        "runtime": runtime,
        "latency_ms": round(latency_ms, 3),
        "status": status,
        "reason": reason,
    }
    with REQUESTS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    _rollup_if_needed(ts)


def _last_rollup_hour() -> datetime | None:
    if not ROLLUP_LOG.exists():
        return None
    lines = [l for l in ROLLUP_LOG.read_text().splitlines() if l.strip()]
    if not lines:
        return None
    data = json.loads(lines[-1])
    return datetime.fromisoformat(data["hour"].replace("Z", "+00:00"))


def _rollup_if_needed(now_ts: float) -> None:
    now = datetime.fromtimestamp(now_ts, tz=timezone.utc)
    prev_hour = (now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1))
    last = _last_rollup_hour()
    if last is None or last < prev_hour:
        _build_rollup(prev_hour)


def _iter_requests(start: datetime, end: datetime):
    if not REQUESTS_LOG.exists():
        return []
    out = []
    with REQUESTS_LOG.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            ts = datetime.fromisoformat(rec["ts_iso"].replace("Z", "+00:00"))
            if start <= ts < end:
                out.append(rec)
    return out


def _build_rollup(hour: datetime) -> None:
    start = hour
    end = hour + timedelta(hours=1)
    rows = _iter_requests(start, end)
    if not rows:
        return
    lat = [r["latency_ms"] for r in rows if r.get("reason") != "invalid_args"]
    by_tool: Dict[str, List[float]] = {}
    err = 0
    for r in rows:
        if r.get("reason") != "invalid_args":
            by_tool.setdefault(r["tool"], []).append(r["latency_ms"])
        if r["status"] != "ok":
            err += 1
    by_tool_stats = {
        t: {"count": len(v), "p95_ms": _percentile(v, 0.95)} for t, v in by_tool.items()
    }
    rec = {
        "hour": hour.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(rows),
        "error_count": err,
        "p50_ms": _percentile(lat, 0.5),
        "p95_ms": _percentile(lat, 0.95),
        "avg_ms": sum(lat) / len(lat) if lat else 0.0,
        "by_tool": by_tool_stats,
    }
    with ROLLUP_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def history(start: datetime, end: datetime) -> List[Dict[str, Any]]:
    if not ROLLUP_LOG.exists():
        return []
    out = []
    with ROLLUP_LOG.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            hour = datetime.fromisoformat(rec["hour"].replace("Z", "+00:00"))
            if start.date() <= hour.date() <= end.date():
                out.append(rec)
    return out


def latest(n: int = 24) -> List[Dict[str, Any]]:
    if not ROLLUP_LOG.exists():
        return []
    lines = [l for l in ROLLUP_LOG.read_text().splitlines() if l.strip()]
    return [json.loads(l) for l in lines[-n:]]


def stats() -> Dict[str, Any]:
    size = REQUESTS_LOG.stat().st_size if REQUESTS_LOG.exists() else 0
    rows = 0
    if ROLLUP_LOG.exists():
        rows = sum(1 for _ in ROLLUP_LOG.open())
    return {"requests_log_size": size, "rollup_rows": rows}
