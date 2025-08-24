import json
import time
from pathlib import Path

SAVE_DIR = Path("logs/savepoints")


def save(moment: str, meta=None) -> dict:
    """Persist a savepoint with a nanosecond timestamp."""

    meta = meta or {}
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.time_ns()
    filename = SAVE_DIR / f"{ts}.json"
    payload = {"moment": moment, "meta": meta, "ts": ts}
    filename.write_text(json.dumps(payload))
    return {"ok": True, "path": str(filename), "ts": ts}


def list_last(n: int = 5):
    """Return the most recent ``n`` savepoints."""

    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for p in SAVE_DIR.iterdir():
        if p.is_file() and p.suffix == ".json":
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.glob("*.json")))
    files.sort()
    data = []
    for p in files[-n:]:
        try:
            info = json.loads(p.read_text())
            info["path"] = str(p)
            data.append(info)
        except Exception:
            continue
    return data
