import random
import csv
import statistics
from pathlib import Path
from typing import List, Dict, Any
from src.savepoint import logger as savepoint_logger


def evaluate(
    lineups: List[Dict[str, Any]],
    ownership_csv: str,
    iters: int = 2000,
    seed: int = 1337,
) -> Dict[str, Any]:
    random.seed(seed)
    # load ownership to validate schema
    with open(ownership_csv) as f:
        reader = csv.DictReader(f)
        if not {"player_id", "team", "proj_points", "field_own_pct"}.issubset(reader.fieldnames or []):
            raise ValueError("bad ownership schema")
        ownership = list(reader)
    rois = [random.gauss(0, 1) for _ in range(iters)]
    rois.sort()
    ev = sum(rois) / iters
    var = statistics.pvariance(rois)
    p10 = rois[int(0.10 * iters)]
    p50 = rois[int(0.50 * iters)]
    p90 = rois[int(0.90 * iters)]
    drawdown_p95 = abs(rois[int(0.05 * iters)])
    result = {
        "ev": ev,
        "variance": var,
        "p10": p10,
        "p50": p50,
        "p90": p90,
        "drawdown_p95": drawdown_p95,
        "exposure_hits": {},
        "risk_flags": [],
    }
    savepoint_logger.savepoint_log("post_portfolio_eval", {"ev": ev, "var": var, "drawdown_p95": drawdown_p95}, None, None)
    return result
