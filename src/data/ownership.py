from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any

from .adapters import base, ownership_dkcsv  # register


def load_daily(path: str | Path, adapter: str = "ownership:dkcsv") -> List[Dict[str, Any]]:
    return base.get(adapter).load(str(path))
