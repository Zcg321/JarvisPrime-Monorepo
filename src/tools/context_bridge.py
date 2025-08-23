import json
from typing import Dict, Any, Optional
from src.core import anchors as anchor_mod


def search(query: str, anchors: Optional[Dict[str, Any]] = None) -> str:
    """Return a snippet from anchors containing the query."""
    if anchors is None:
        anchors = anchor_mod.load_all()
    if not query:
        return ""
    q = query.lower()
    for content in anchors.values():
        text = content if isinstance(content, str) else json.dumps(content)
        for line in text.splitlines():
            if q in line.lower():
                return line.strip()
    return ""
