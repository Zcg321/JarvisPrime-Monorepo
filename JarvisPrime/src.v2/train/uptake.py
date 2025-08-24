import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

LOG_DIR = Path("logs/experience")


def record(example: Dict[str, Any]) -> str:
    """Persist a single experience example.

    A nanosecond timestamp is used for both the filename and the ``ts`` field
    to avoid collisions when multiple events occur within the same second.
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.time_ns()
    data = dict(example)
    data.setdefault("ts", ts)
    path = LOG_DIR / f"{ts}.json"
    path.write_text(json.dumps(data))
    return str(path)


def list_last(n: int = 5):
    """Return the most recent ``n`` recorded experiences."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(LOG_DIR.glob("*.json"))
    data = []
    for p in files[-n:]:
        try:
            data.append(json.loads(p.read_text()))
        except Exception:
            continue
    return data


def replay(n: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return experiences in chronological order.

    Parameters
    ----------
    n: optional int
        If provided, limit to the first ``n`` experiences.  ``None`` returns
        all available logs.
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(LOG_DIR.glob("*.json"))
    if n is not None:
        files = files[:n]
    data = []
    for p in files:
        try:
            data.append(json.loads(p.read_text()))
        except Exception:
            continue
    return data


def search(query: str, n: int = 5) -> List[Dict[str, Any]]:
    """Return up to ``n`` most recent experiences containing ``query``.

    The search is case-insensitive and scans the serialized JSON of each
    experience.  Results are returned in chronological order from oldest to
    newest among the matches.
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(LOG_DIR.glob("*.json"), reverse=True)
    results: List[Dict[str, Any]] = []
    q = query.lower()
    for p in files:
        if len(results) >= n:
            break
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        if q in json.dumps(data).lower():
            results.append(data)
    return list(reversed(results))


def stats() -> Dict[str, int]:
    """Return basic statistics about recorded experiences.

    The result contains the total number of experience files and the
    timestamp of the most recent entry (``last_ts``).  If no experiences
    exist yet, ``last_ts`` is ``0``.
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(LOG_DIR.glob("*.json"))
    if not files:
        return {"count": 0, "last_ts": 0}
    last = files[-1]
    try:
        last_ts = int(last.stem)
    except ValueError:
        last_ts = 0
    return {"count": len(files), "last_ts": last_ts}
