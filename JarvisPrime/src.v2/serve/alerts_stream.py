import json
import time
from pathlib import Path
from typing import Iterator

from src.serve import alerts

# Simple generator for Server-Sent Events.
# It yields existing alerts then polls for new ones.

def stream_events(start_ts: float = 0.0) -> Iterator[str]:
    last = start_ts
    while True:
        records = alerts.get_last(1000, since=last)
        for rec in records:
            if rec.get("ts", 0) > last:
                last = rec["ts"]
                yield f"data: {json.dumps(rec)}\n\n"
        time.sleep(0.5)
