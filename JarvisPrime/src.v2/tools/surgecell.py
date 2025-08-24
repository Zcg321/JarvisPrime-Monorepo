"""SurgeCell allocation helper."""

import json
from pathlib import Path
from typing import Dict

from src.core import anchors

DEFAULT = anchors.surge_allocations(anchors.load_all()['boot'])
LOG_PATH = Path("logs/savepoints/surgecell_last.json")


def load_last() -> Dict[str, float]:
    """Return the last persisted allocation or the default."""
    try:
        return json.loads(LOG_PATH.read_text())
    except Exception:
        return DEFAULT.copy()


def allocate(weights: Dict[str, float] = None, history: Dict[str, float] = None) -> Dict[str, float]:
    """Return normalized weights optionally adjusted by recent usage history.

    The final allocation is persisted to ``logs/savepoints/surgecell_last.json``
    so subsequent runs can resume from the latest state.
    """

    w = load_last()
    if weights:
        w.update({k: v for k, v in weights.items() if k in w})
    if history:
        for k in w:
            w[k] = w[k] / (1 + history.get(k, 0))
    total = sum(w.values()) or 1.0
    norm = {k: v / total for k, v in w.items()}
    rounded = {k: round(v, 2) for k, v in norm.items()}
    diff = round(1.0 - sum(rounded.values()), 2)
    first_key = next(iter(rounded))
    rounded[first_key] = round(rounded[first_key] + diff, 2)

    # persist last allocation
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text(json.dumps(rounded))
    except Exception:
        pass

    return rounded
