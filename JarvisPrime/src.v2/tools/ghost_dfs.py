import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.tools.ghost import token_dir, deterministic_seed, LEGACY_ROOT

DATA_DIR = LEGACY_ROOT
ROI_LOG = LEGACY_ROOT / "roi.jsonl"
ROSTER_CLASSIC = ["PG", "SG", "SF", "PF", "C", "G", "F", "UTIL"]


def _rng(seed: int, slate_id: str, token_id: str) -> random.Random:
    return random.Random(deterministic_seed(token_id, slate_id, seed))


def seed_pool(
    slate_id: str,
    seed: int,
    pool_size: int = 50,
    token_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    token_id = token_id or "anon"
    rng = _rng(seed, slate_id, token_id)
    dir_path = token_dir(token_id)
    pool: List[Dict[str, Any]] = []
    for i in range(pool_size):
        lineup = []
        total = 0
        for pos in ROSTER_CLASSIC:
            sal = rng.randint(4000, 8000)
            total += sal
            lineup.append({"player": f"P{rng.randint(1,999)}", "pos": pos, "salary": sal})
        if total > 50000:
            diff = total - 50000
            lineup[-1]["salary"] -= diff
            total = 50000
        pool.append({
            "lineup_id": f"L{i}",
            "players": lineup,
            "salary_total": total,
            "leftover": 50000 - total,
        })
    (dir_path / f"{slate_id}_{seed}_seed.json").write_text(json.dumps(pool))
    return pool


def mutate_pool(
    slate_id: str,
    seed: int,
    constraints: Optional[Dict[str, Any]] = None,
    cap: int = 50000,
    token_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    constraints = constraints or {}
    token_id = token_id or "anon"
    dir_path = token_dir(token_id)
    file = dir_path / f"{slate_id}_{seed}_seed.json"
    if file.exists():
        pool = json.loads(file.read_text())
    else:
        legacy = DATA_DIR / f"{slate_id}_{seed}_seed.json"
        if legacy.exists():
            pool = json.loads(legacy.read_text())
        else:
            pool = seed_pool(slate_id, seed, token_id=token_id)
    rng = _rng(seed + 1, slate_id, token_id)
    mutated: List[Dict[str, Any]] = []
    for item in pool:
        lineup = item["players"]
        total = sum(p["salary"] for p in lineup)
        if total > cap:
            diff = total - cap
            lineup[-1]["salary"] -= diff
            total = cap
        leftover = cap - total
        mutated.append({
            "lineup_id": item["lineup_id"],
            "players": lineup,
            "salary_total": total,
            "leftover": leftover,
        })
    return mutated


def roi_log(
    slate_id: str, lineup_id: str, entries: int, profit: float, token_id: Optional[str] = None
) -> None:
    token_id = token_id or "anon"
    log_path = token_dir(token_id) / "roi.jsonl"
    rec = {
        "slate_id": slate_id,
        "lineup_id": lineup_id,
        "entries": entries,
        "profit": profit,
    }
    with log_path.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    if os.environ.get("ROI_LOG_COMPAT_MIRROR") == "1":
        with ROI_LOG.open("a") as f:
            f.write(json.dumps(rec) + "\n")
