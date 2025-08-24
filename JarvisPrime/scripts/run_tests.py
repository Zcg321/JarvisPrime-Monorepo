#!/usr/bin/env python3
"""Minimal pytest runner emitting JSON summary.

MIT License (c) 2025 Zack
"""
import json, os, time, sys
from pathlib import Path


def main() -> int:
    os.makedirs("logs", exist_ok=True)
    t0 = time.time()
    try:
        import pytest
    except Exception as e:
        summary = {"passed": 0, "failed": 0, "xfailed": 0, "duration": 0.0, "error": "pytest_not_installed"}
        Path("logs/test_summary.json").write_text(json.dumps(summary, indent=2))
        print("pytest missing:", e)
        return 1
    args = ["-q", "tests"]
    rc = pytest.main(args)
    duration = round(time.time() - t0, 3)
    passed = 0
    failed = 0
    if rc == 0:
        try:
            for p in Path("tests").rglob("test_*.py"):
                text = p.read_text(encoding="utf-8", errors="ignore")
                passed += text.count("def test_")
        except Exception:
            passed = 1
    else:
        failed = 1
    summary = {"passed": passed, "failed": failed, "xfailed": 0, "duration": duration}
    Path("logs/test_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))
    return rc


if __name__ == "__main__":
    sys.exit(main())
