import math
from typing import List, Dict, Optional
from pathlib import Path
import json
import yaml
from src.savepoint import logger as savepoint_logger

def _read_policy() -> Dict[str, float]:
    path = Path("configs/bankroll.yaml")
    if path.exists():
        try:
            return yaml.safe_load(path.read_text()) or {}
        except Exception:
            return {}
    return {}

def allocate(
    bankroll: float,
    slates: List[Dict[str, any]],
    unit_fraction: Optional[float] = None,
    seed: int = 0,
) -> Dict[str, any]:
    policy = _read_policy()
    uf = unit_fraction if unit_fraction is not None else policy.get("unit_fraction", 0.02)
    allocations = []
    remaining = bankroll
    for s in slates:
        edge = max(min(float(s.get("edge_hint", 0.0)), 0.3), -0.1)
        stake = bankroll * uf * max(edge, 0.0)
        fee = float(s["avg_entry_fee"])
        max_entries = int(stake // fee)
        entries = min(int(s["entries"]), max_entries)
        allocations.append({"slate_id": s["id"], "entries": entries})
        remaining -= entries * fee
    savepoint_logger.savepoint_log(
        "post_bankroll_alloc",
        {"allocations": allocations, "bankroll": bankroll},
        None,
        bankroll,
    )
    return {"allocations": allocations, "remaining": round(remaining, 2)}
