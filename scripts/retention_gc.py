#!/usr/bin/env python3
"""Retention garbage collector."""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

CFG_PATH = Path("configs/retention.yaml")
GC_LOG = Path("logs/gc/gc.jsonl")
GC_LOG.parent.mkdir(parents=True, exist_ok=True)


def load_cfg():
    with CFG_PATH.open() as f:
        return yaml.safe_load(f) or {}


def tombstone(path: Path):
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "path": str(path),
    }
    with GC_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def gc(dry_run: bool = True) -> int:
    cfg = load_cfg()
    removed = 0
    for entry in cfg.get("paths", []):
        p = Path(entry.get("path", ""))
        days = int(entry.get("days", 0))
        cutoff = time.time() - days * 86400
        for file in p.glob("**/*"):
            if not file.is_file():
                continue
            if file.stat().st_mtime < cutoff:
                if dry_run:
                    print(f"DRY {file}")
                else:
                    try:
                        file.unlink()
                        tombstone(file)
                        removed += 1
                    except OSError:
                        pass
    return removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()
    if args.confirm:
        gc(dry_run=False)
    else:
        gc(dry_run=True)


if __name__ == "__main__":
    main()
