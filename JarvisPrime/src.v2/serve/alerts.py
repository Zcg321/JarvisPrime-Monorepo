import json
import time
from pathlib import Path
from typing import List, Optional

from src.config.loader import load_config
from src.serve import logging as slog
from src.savepoint import logger as splog
from src.serve import metrics

ALERT_PATH = Path("logs/alerts/alerts.jsonl")
NOTIFY_LOG = Path("logs/alerts/notify.log")

CFG = load_config().get("alerts", {})
SUBS = CFG.get("subscriptions", [])
WEBHOOKS = CFG.get("webhooks", [])
TTL_DAYS = 30
_INDEX: dict | None = None
_INDEX_PATH: Path | None = None
ROTATE_SIZE = 10 * 1024 * 1024
ROTATE_KEEP = 5

SEVERITY_MAP = {
    "policy": "WARN",
    "policy_deny": "WARN",
    "risk_gate": "WARN",
    "risk": "WARN",
    "slo": "ERROR",
    "slo_breach": "ERROR",
    "compliance": "INFO",
    "compliance_purge": "INFO",
    "compliance_export": "INFO",
    "cohort_drift": "WARN",
}


def log_event(
    event_type: str,
    reason: str,
    role: str | None = None,
    lineage_id: str | None = None,
    severity: str | None = None,
    _check_escalation: bool = True,
) -> None:
    ALERT_PATH.parent.mkdir(parents=True, exist_ok=True)
    severity = severity or SEVERITY_MAP.get(event_type, "INFO")
    rec = {
        "ts": time.time(),
        "type": event_type,
        "reason": reason,
        "severity": severity,
    }
    if role:
        rec["role"] = role
    if lineage_id:
        rec["lineage_id"] = lineage_id
    with ALERT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    metrics.METRICS.alerts_file_size = ALERT_PATH.stat().st_size
    _rotate()
    global _INDEX
    _INDEX = None
    if severity == "ERROR":
        try:
            splog.savepoint_log(
                "alert_event",
                {"type": event_type, "reason": reason},
            )
        except Exception:
            pass
    for sub in SUBS:
        if event_type in sub.get("types", []):
            msg = {
                "ts": rec["ts"],
                "type": event_type,
                "severity": severity,
                "reason": reason,
                "notify": sub.get("notify"),
            }
            target = sub.get("notify")
            if target == "stdout":
                print(json.dumps(msg))
            else:
                NOTIFY_LOG.parent.mkdir(parents=True, exist_ok=True)
                with NOTIFY_LOG.open("a", encoding="utf-8") as nf:
                    nf.write(json.dumps(msg) + "\n")
            slog.alert(
                f"{event_type}",
                component="alerts",
                severity=severity,
                notify=target,
            )
    for wh in WEBHOOKS:
        if severity in wh.get("severities", []) and event_type in wh.get("types", []):
            payload = {
                "ts": rec["ts"],
                "severity": severity,
                "type": event_type,
                "reason": reason,
            }
            if lineage_id:
                payload["lineage_id"] = lineage_id
            try:
                import urllib.request

                req = urllib.request.Request(
                    wh.get("url"),
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=2)
            except Exception as e:
                slog.log(
                    "WARN",
                    "webhook failed",
                    component="alerts",
                    url=wh.get("url"),
                    error=str(e),
                )
    if severity == "ERROR" and _check_escalation:
        since = time.time() - 600
        errors = [
            r
            for r in get_last(1000, since=since)
            if r.get("severity") == "ERROR" and r.get("type") != "escalation"
        ]
        if len(errors) > 5:
            log_event(
                "escalation",
                "error flood",
                severity="ERROR",
                _check_escalation=False,
            )


def _read_all() -> List[dict]:
    if not ALERT_PATH.exists():
        return []
    with ALERT_PATH.open(encoding="utf-8") as f:
        lines = f.readlines()
    cutoff = time.time() - TTL_DAYS * 86400
    kept = []
    for ln in lines:
        try:
            rec = json.loads(ln)
        except Exception:
            continue
        if rec.get("ts", 0) >= cutoff:
            kept.append(rec)
    if len(kept) != len(lines):
        with ALERT_PATH.open("w", encoding="utf-8") as f:
            for rec in kept:
                f.write(json.dumps(rec) + "\n")
    return kept


def _build_index() -> dict:
    records = _read_all()
    by_sev: dict[str, List[dict]] = {}
    by_type: dict[str, List[dict]] = {}
    for rec in records:
        by_sev.setdefault(rec.get("severity", "INFO"), []).append(rec)
        by_type.setdefault(rec.get("type"), []).append(rec)
    global _INDEX_PATH
    _INDEX_PATH = ALERT_PATH
    return {"records": records, "by_sev": by_sev, "by_type": by_type}


def _rotate() -> None:
    if not ALERT_PATH.exists():
        return
    size = ALERT_PATH.stat().st_size
    if size <= ROTATE_SIZE:
        return
    for i in range(ROTATE_KEEP - 1, 0, -1):
        src = ALERT_PATH.with_name(f"alerts.jsonl.{i}")
        dst = ALERT_PATH.with_name(f"alerts.jsonl.{i+1}")
        if src.exists():
            if i == ROTATE_KEEP - 1 and dst.exists():
                dst.unlink()
            src.rename(dst)
    ALERT_PATH.rename(ALERT_PATH.with_name("alerts.jsonl.1"))
    ALERT_PATH.touch()
    metrics.METRICS.alerts_rotations += 1
    metrics.METRICS.alerts_file_size = ALERT_PATH.stat().st_size


def _needs_rebuild() -> bool:
    return _INDEX is None or _INDEX_PATH != ALERT_PATH


def get_last(
    n: int = 50, since: Optional[float] = None, severity: str | None = None
) -> List[dict]:
    global _INDEX
    if _needs_rebuild():
        _INDEX = _build_index()
    records = _INDEX["records"]
    out = []
    for rec in records:
        if since and rec.get("ts", 0) < since:
            continue
        if severity and rec.get("severity") != severity:
            continue
        out.append(rec)
    return out[-n:]


def counts_by_severity() -> dict:
    return summary()["severity"]


def summary() -> dict:
    global _INDEX
    if _needs_rebuild():
        _INDEX = _build_index()
    by_sev = {k: len(v) for k, v in _INDEX["by_sev"].items()}
    for key in ["INFO", "WARN", "ERROR"]:
        by_sev.setdefault(key, 0)
    by_type = {k: len(v) for k, v in _INDEX["by_type"].items() if k}
    return {"severity": by_sev, "type": by_type}
