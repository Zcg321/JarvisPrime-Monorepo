import json
import os
import socket
import time
import uuid
from pathlib import Path
from typing import Tuple

from src.reflex import policy

BASE = Path("logs/savepoints")


def _pointer_path(token: str, tool: str) -> Path:
    return BASE / token / "__last" / f"{tool}.json"


def next_ids(tool: str) -> Tuple[str, str | None]:
    token = policy.current_token() or "anon"
    p = _pointer_path(token, tool)
    p.parent.mkdir(parents=True, exist_ok=True)
    parent = None
    try:
        parent = json.loads(p.read_text()).get("lineage_id")
    except Exception:
        parent = None
    seed = f"{socket.gethostname()}:{time.time()}:{token}:{tool}"
    lineage_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))
    tmp = p.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"lineage_id": lineage_id}, f)
    os.replace(tmp, p)
    return lineage_id, parent
