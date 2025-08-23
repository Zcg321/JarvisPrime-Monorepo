"""Append-only ancestry log for Reflex decisions.

MIT License.
Copyright (c) 2025 Zack
"""
from pathlib import Path
from src.core.logio import append_jsonl_rotating

ANCESTRY_FILE = Path("logs/reflex_ancestry.jsonl")


def append(entry: dict) -> None:
    append_jsonl_rotating(str(ANCESTRY_FILE), entry)
