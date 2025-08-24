import json
import hashlib
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from src.core import anchors
from . import lineage
from src.reflex import policy

LOG_DIR = Path("logs/savepoints")
REDACT_KEYS = {"token", "api", "secret"}
MAX_KEEP = 500
MAX_DAYS = 14


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: ("[REDACTED]" if k.lower() in REDACT_KEYS else _redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


def savepoint_log(
    event: str,
    payload: Dict[str, Any],
    affect: Optional[str] = None,
    bankroll: Optional[float] = None,
    token_id: Optional[str] = None,
) -> tuple[Path, str]:
    token = token_id or policy.current_token()
    log_dir = LOG_DIR / token if token != "anon" else LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = time.gmtime()
    stamp = time.strftime("%Y%m%d_%H%M%S", ts)
    ts_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", ts)
    safe_event = "".join(c if c.isalnum() or c in "-_" else "_" for c in event) or "event"
    redacted = _redact(payload or {})
    payload_json = json.dumps(redacted, sort_keys=True, separators=(",", ":"))
    sha = hashlib.sha256(payload_json.encode()).hexdigest()
    lineage_id, parent_id = lineage.next_ids(event)
    data = {
        "event": event,
        "ts_iso": ts_iso,
        "anchors": anchors.load_all(),
        "affect": affect,
        "bankroll": bankroll,
        "payload": redacted,
        "sha256_payload": sha,
        "lineage_id": lineage_id,
        "parent_id": parent_id,
    }
    data["token_id"] = token
    data["policy_version"] = policy.policy_version()
    fname = log_dir / f"{stamp}_{safe_event}.json"
    tmp = fname.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, sort_keys=True)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(tmp, fname)
    try:
        rotate_logs(MAX_KEEP, MAX_DAYS)
    except Exception:
        pass
    return fname, lineage_id


def rotate_logs(keep: int = MAX_KEEP, days: int = MAX_DAYS) -> int:
    """Delete savepoints exceeding ``keep`` or older than ``days``."""

    files = sorted(LOG_DIR.glob("**/*.json"))
    cutoff = time.time() - days * 86400
    remove = files[:-keep] if len(files) > keep else []
    for f in files:
        try:
            if f.stat().st_mtime < cutoff:
                remove.append(f)
        except OSError:
            continue
    removed = 0
    for f in set(remove):
        try:
            f.unlink()
            removed += 1
        except OSError:
            pass
    return removed
