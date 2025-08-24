import hashlib
from typing import Dict, Tuple


def infer_repo_branch(task_card: str, routing_policies: Dict[str, dict], default_repo: dict) -> Tuple[str, str, str]:
    """Infer repo/branch from task text using simple token matching.

    Returns (repo, branch, reason).
    """
    text = task_card.lower()
    best = None
    best_score = 0
    reason = "default"
    for name, pol in routing_policies.items():
        tokens = [t.lower() for t in pol.get("tokens", [])]
        weight = pol.get("weight", 1)
        score = 0
        for t in tokens:
            if t in text:
                score += text.count(t)
        score *= weight
        if score > best_score:
            best = pol
            best_score = score
            reason = f"matched:{name}"
    if not best:
        best = default_repo
    return best["repo"], best.get("branch", "main"), reason
