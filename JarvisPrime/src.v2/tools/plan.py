import json
import pathlib
from typing import List, Dict, Any


CONFIG_DIR = pathlib.Path(__file__).resolve().parents[2] / "configs" / "ascension"


def _load_phases() -> List[Dict[str, Any]]:
    phases: List[Dict[str, Any]] = []
    if CONFIG_DIR.exists():
        for p in sorted(CONFIG_DIR.glob("phase_*.json")):
            try:
                phases.append(json.loads(p.read_text()))
            except Exception:
                continue
    return phases


def generate(query: str, anchors: Dict[str, Any] = None) -> List[Dict[str, str]]:
    """Generate action steps from the ascension path.

    Parameters
    ----------
    query: str
        Optional keyword filter applied to actions (case-insensitive).
    anchors: dict, optional
        Anchor data loaded via ``src.core.anchors.load_all``. Used only if
        ascension configs are missing.

    Returns
    -------
    list of dict
        Each entry contains ``phase`` and ``action`` keys.
    """
    path = _load_phases()
    if not path and anchors:
        path = anchors.get("ascension", {}).get("reversed_path", [])
    q = (query or "").lower()
    steps: List[Dict[str, str]] = []
    for phase in path:
        phase_name = phase.get("phase", "")
        actions = phase.get("actions") or phase.get("tasks", [])
        for action in actions:
            if not q or any(word in action.lower() for word in q.split()):
                steps.append({"phase": phase_name, "action": action})
    if not steps:
        for phase in path:
            phase_name = phase.get("phase", "")
            for action in (phase.get("actions") or phase.get("tasks", [])):
                steps.append({"phase": phase_name, "action": action})
    return steps
