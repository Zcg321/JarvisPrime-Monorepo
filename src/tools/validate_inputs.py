"""Validate ownership, results, and lineup inputs."""
from __future__ import annotations

import csv
import json
from typing import List, Dict, Any
from pathlib import Path

from src.savepoint import logger


def validate(ownership_csv: str, results_csv: str | None, lineups: List[Dict[str, Any]]):
    ownership_ids = set()
    with open(ownership_csv, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            ownership_ids.add(row.get("player_id"))
    missing_from_ownership = set()
    salary_violations = 0
    for lu in lineups:
        ids = [p.get("player_id") for p in lu.get("players", [])]
        missing_from_ownership.update(i for i in ids if i not in ownership_ids)
        salary = sum(p.get("salary", 0) for p in lu.get("players", []))
        if salary > 50000:
            salary_violations += 1
    results_missing = set()
    if results_csv:
        with open(results_csv, newline="") as fh:
            reader = csv.DictReader(fh)
            result_ids = {row.get("player_id") for row in reader}
        results_missing = ownership_ids - result_ids
    report = {
        "missing_from_ownership": sorted(missing_from_ownership),
        "salary_violations": salary_violations,
        "results_missing": sorted(results_missing),
    }
    logger.savepoint_log("post_validate_inputs", report, None, None)
    return report
