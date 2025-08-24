import fnmatch
import yaml
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = ROOT / "foreman" / "policy.yaml"

if POLICY_FILE.exists():
    POLICY = yaml.safe_load(POLICY_FILE.read_text())
else:
    POLICY = {"repos": {}, "defaults": {"max_files": 15, "max_runtime_sec": 900}}


def _rules_for(repo: str) -> dict:
    return POLICY.get("repos", {}).get(repo, POLICY.get("defaults", {}))


def get_limits(repo: str) -> dict:
    return _rules_for(repo)


def validate_plan(files: List, repo: str | None) -> None:
    repo_rules = _rules_for(repo or "")
    max_files = repo_rules.get("max_files", POLICY.get("defaults", {}).get("max_files", 15))
    if len(files) > max_files:
        raise ValueError(f"plan touches {len(files)} files; limit {max_files}")
    allow = repo_rules.get("allow_paths")
    deny = repo_rules.get("deny_paths", [])
    for f in files:
        path = f.path if hasattr(f, "path") else f.get("path")
        if any(fnmatch.fnmatch(path, d) for d in deny):
            raise ValueError(f"path {path} denied by policy")
        if allow and not any(fnmatch.fnmatch(path, a) for a in allow):
            raise ValueError(f"path {path} not in allow list")
