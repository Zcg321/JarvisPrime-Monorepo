"""DFS calibration metrics.

MIT License (c) 2025 Zack
"""
from collections import Counter
from typing import Dict, List

def uniqueness_score(players: List[Dict[str, float]]) -> Dict[str, float]:
    counts = Counter(p.get("name") for p in players)
    total = len(players) or 1
    return {name: 1 - c / total for name, c in counts.items()}

def diversity_score(players: List[Dict[str, float]]) -> float:
    teams = {p.get("team") for p in players if p.get("team")}
    return len(teams) / (len(players) or 1)

def risk_score(lineup: List[Dict[str, float]]) -> float:
    vals = [p.get("proj", 0.0) for p in lineup]
    if not vals:
        return 0.0
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / len(vals)
    return var
