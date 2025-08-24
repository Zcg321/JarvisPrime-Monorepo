import json
import time
import os
from pathlib import Path

LOG_PATH = Path("logs/server.log")
MAX_BYTES = 10 * 1024 * 1024
MAX_FILES = 10
LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
CURRENT_LEVEL = LEVELS.get(os.environ.get("LOG_LEVEL", "INFO").upper(), 20)


def _rotate() -> None:
    if LOG_PATH.exists() and LOG_PATH.stat().st_size >= MAX_BYTES:
        for i in range(MAX_FILES - 1, 0, -1):
            src = LOG_PATH.with_name(f"server.log.{i}")
            dst = LOG_PATH.with_name(f"server.log.{i+1}")
            if src.exists():
                if i + 1 >= MAX_FILES:
                    src.unlink()
                else:
                    src.rename(dst)
        LOG_PATH.rename(LOG_PATH.with_name("server.log.1"))


def log(level: str, msg: str, component: str = "server", **extra) -> None:
    if LEVELS.get(level.upper(), 20) < CURRENT_LEVEL:
        return
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _rotate()
    rec = {"ts": time.time(), "level": level, "msg": msg, "component": component}
    rec.update({k: v for k, v in extra.items() if v is not None})
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def alert(
    msg: str, component: str = "server", severity: str | None = None, notify: str | None = None, **extra
) -> None:
    """Log a structured ALERT line."""
    log("ALERT", msg, component, severity=severity, notify=notify, **extra)
