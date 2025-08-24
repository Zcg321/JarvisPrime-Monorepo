from __future__ import annotations

import json
import time
from pathlib import Path

from src.serve import alerts


def check_drift() -> float:
    start_wall = time.time()
    start_mono = time.monotonic()
    time.sleep(0.1)
    drift = abs((time.time() - start_wall) - (time.monotonic() - start_mono))
    if drift > 2:
        alerts.log_event("clock_drift", f"drift {drift:.2f}s", severity="WARN")
    return drift


def main():
    drift = check_drift()
    Path("logs/alerts").mkdir(parents=True, exist_ok=True)
    print(json.dumps({"drift": drift}))


if __name__ == "__main__":
    main()
