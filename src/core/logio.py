"""JSONL logging with rotation.

MIT License (c) 2025 Zack
"""
import json
from pathlib import Path


def _rotate_if_needed(path: Path, max_bytes: int) -> None:
    try:
        if path.exists() and path.stat().st_size >= max_bytes:
            base = str(path)
            n = 1
            while Path(f"{base}.part{n}").exists():
                n += 1
            path.rename(Path(f"{base}.part{n}"))
    except Exception:
        pass


def append_jsonl_rotating(path_str: str, obj: dict, max_bytes: int = 10_000_000) -> None:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    _rotate_if_needed(path, max_bytes)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
