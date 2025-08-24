from typing import List, Dict
import fnmatch


def _match(name: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def allowed(role: str, tool: str, policies: List[Dict]) -> bool:
    for p in policies:
        if p.get("role") == role:
            allow = p.get("allow", [])
            deny = p.get("deny", [])
            if _match(tool, deny):
                return False
            if allow and not _match(tool, allow):
                return False
    return True
