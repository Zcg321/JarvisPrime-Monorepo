"""Unified JSON error helpers.

MIT License (c) 2025 Zack
"""
from typing import Any, Dict

def json_error(code: str, http: int, **extra: Any) -> Dict[str, Any]:
    obj: Dict[str, Any] = {"error": code}
    if extra:
        obj.update(extra)
    obj["status_code"] = http
    return obj
