"""Runtime auto-selection utilities."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict


def decide_runtime(stats: Dict[str, Dict[str, float]] | None) -> str:
    if not stats:
        return "int8"
    fp = stats.get("fp16", {}).get("p95_ms", float("inf"))
    it = stats.get("int8", {}).get("p95_ms", float("inf"))
    return "int8" if it <= fp else "fp16"


def decide_runtime_from_logs(compare_path: str = "logs/perf/compare.json") -> str:
    if Path(compare_path).exists():
        try:
            data = json.loads(Path(compare_path).read_text())
        except Exception:
            data = None
    else:
        data = None
    return decide_runtime(data)


def init_runtime(env_val: str) -> str:
    runtime = env_val
    if env_val == "auto":
        runtime = decide_runtime_from_logs()
    Path("logs/perf").mkdir(parents=True, exist_ok=True)
    Path("logs/perf/auto_runtime.json").write_text(
        json.dumps({"runtime": runtime, "ts": time.time()})
    )
    return runtime
