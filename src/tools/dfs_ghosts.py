"""Ghost lineup utilities."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Optional

GHOST_FILE = Path("logs/dfs_ghosts.jsonl")


def seed(lineups_from: str, k: int, slate_id: str, note: Optional[str] = None):
    """Record metadata about seeded ghost lineups.

    This stub simply appends an entry describing the request and returns the
    number of ghosts seeded.  The full engine can later use this log to inject
    historical +EV constructions.
    """
    GHOST_FILE.parent.mkdir(parents=True, exist_ok=True)
    obj = {"lineups_from": lineups_from, "k": k, "slate_id": slate_id, "note": note}
    with GHOST_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")
    return {"seeded": k}


def inject(
    k: int,
    mutate_rate: float,
    salary_cap: float,
    roster_slots: Optional[Dict[str, int]],
    max_from_team: Optional[int],
    seed: Optional[int] = None,
):
    """Return up to ``k`` ghost lineups.

    For the stub we return placeholder lineups using deterministic naming based
    on the seed.  Real implementations could mutate stored ghosts and enforce
    salary/roster constraints.
    """
    rng = random.Random(seed)
    ghosts: List[List[Dict[str, float]]] = []
    for i in range(max(0, k)):
        ghosts.append([{"name": f"Ghost{rng.randint(0, 999)}", "slot": "GHOST"}])
    return {"ghosts": ghosts}
