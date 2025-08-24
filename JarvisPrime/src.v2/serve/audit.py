import json
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, Optional

LOG_DIR = Path("logs/audit")
LOG_FILE = LOG_DIR / "audit.jsonl"
MAX_LINES = 100_000
REDACT_KEYS = {"token", "secret", "api", "password"}

_line_count = 0

def _init() -> None:
    global _line_count
    if LOG_FILE.exists():
        try:
            with LOG_FILE.open("r", encoding="utf-8") as f:
                _line_count = sum(1 for _ in f)
        except Exception:
            _line_count = 0

_init()


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: ("[REDACTED]" if k.lower() in REDACT_KEYS else _redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


def _rotate_if_needed() -> None:
    global _line_count
    if _line_count < MAX_LINES:
        return
    base = LOG_FILE
    n = 1
    while base.with_suffix(f".part{n}").exists():
        n += 1
    try:
        base.rename(base.with_suffix(f".part{n}"))
    except Exception:
        pass
    _line_count = 0


def record(tool: str, args: Dict[str, Any], token: Optional[str], token_id: Optional[str], status: int) -> None:
    global _line_count
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _rotate_if_needed()
    redacted = _redact(args or {})
    rec = {
        "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": tool,
        "args_redacted": redacted,
        "result_status": status,
    }
    if token:
        rec["auth_token_hash"] = hashlib.sha256(token.encode()).hexdigest()
    if token_id:
        rec["token_id"] = token_id
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    _line_count += 1
