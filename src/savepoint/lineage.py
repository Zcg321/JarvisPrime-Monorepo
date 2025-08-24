import uuid
from typing import Dict, Optional, Tuple

_last: Dict[str, str] = {}


def next_ids(tool: str) -> Tuple[str, Optional[str]]:
    parent = _last.get(tool)
    lineage_id = str(uuid.uuid4())
    _last[tool] = lineage_id
    return lineage_id, parent
