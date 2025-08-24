import hashlib
import random
import os
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import contextmanager

try:  # pragma: no cover - platform specific
    import fcntl  # type: ignore
except Exception:  # pragma: no cover
    fcntl = None


def dfs_sim(lineup: List[Dict], sims: int = 1000, seed: Optional[int] = None) -> Dict[str, float]:
    """Simulate DFS outcomes for a lineup.

    A local ``random.Random`` instance is optionally seeded for deterministic
    unit tests without affecting global state.
    """
    if not lineup:
        return {"mean": 0.0, "stdev": 0.0, "p95": 0.0}
    rng = random.Random(seed)
    totals = [
        sum(p.get("proj", 0) + rng.gauss(0, 1) for p in lineup)
        for _ in range(max(1, sims))
    ]
    totals.sort()
    n = len(totals)
    mean = sum(totals) / n
    stdev = (sum((x - mean) ** 2 for x in totals) / n) ** 0.5
    p95 = totals[int(0.95 * (n - 1))]
    return {"mean": mean, "stdev": stdev, "p95": p95}


LEGACY_ROOT = Path(os.environ.get("ROI_LOG_DIR_LEGACY", "logs/ghosts"))
TOKEN_ROOT = Path(os.environ.get("ROI_LOG_DIR_TOKENIZED", "logs/ghosts"))


def token_dir(token_id: Optional[str]) -> Path:
    """Return per-token ghost directory creating it if needed."""
    d = TOKEN_ROOT / (token_id or "anon")
    d.mkdir(parents=True, exist_ok=True)
    return d


@contextmanager
def lock_token(token_id: str):
    """File lock for a token's ghost directory."""
    path = token_dir(token_id) / ".lock"
    with open(path, "w") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_UN)


def deterministic_seed(token_id: str, slate_id: str, seed: int) -> int:
    """Stable hash combining token, slate and seed."""
    h = hashlib.sha256(f"{token_id}:{slate_id}:{seed}".encode()).hexdigest()
    return int(h[:8], 16)
