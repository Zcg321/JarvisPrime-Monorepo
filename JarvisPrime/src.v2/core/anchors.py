import json
import pathlib
import re
from typing import Dict, Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DNA_DIR = ROOT / 'data' / 'dna'
ANCHOR_DIR = ROOT / 'anchors'

ENDGAME_FILE = DNA_DIR / 'continuum_true_endgame.json'
ASCENSION_FILE = DNA_DIR / 'continuum_ascension_path.json'
MASTER_FILE = DNA_DIR / 'continuum_master_final.json'
BOOT_FILE = DNA_DIR / 'JarvisPrime_BootProtocol.md'


def _load_json(path: pathlib.Path) -> Dict[str, Any]:
    text = path.read_text().replace('\u00a0', ' ')
    return json.loads(text)


def _load_text(path: pathlib.Path) -> str:
    return path.read_text()


def load_all() -> Dict[str, Any]:
    """Load all anchor files into memory."""
    data = {
        'endgame': _load_json(ENDGAME_FILE),
        'ascension': _load_json(ASCENSION_FILE),
        'master': _load_json(MASTER_FILE),
        'boot': _load_text(BOOT_FILE),
    }
    text_anchors: Dict[str, str] = {}
    if ANCHOR_DIR.exists():
        for path in ANCHOR_DIR.glob('*.md'):
            try:
                text_anchors[path.stem] = _load_text(path)
            except Exception:
                continue
    if text_anchors:
        data['anchors_md'] = text_anchors
    return data


def kill_phrase(boot_text: str) -> str:
    """Extract kill phrase from Boot Protocol."""
    m = re.search(r'Kill Phrase\n([^\n]+)', boot_text)
    return m.group(1).split('\u2192')[0].strip().lower() if m else 'lights out, jarvis'


def surge_allocations(boot_text: str) -> Dict[str, float]:
    """Parse SurgeCell allocations from the Boot Protocol text.

    The Boot Protocol line looks like::

        SurgeCell — DFS 30% | Mirror 30% | Reflex 20% | Ghost 10% | TrAId 10%

    Returns a mapping with decimal weights.
    """
    m = re.search(r'SurgeCell[^\n]*', boot_text)
    if not m:
        return {"DFS": 0.30, "VoiceMirror": 0.30, "Reflex": 0.20, "Ghost": 0.10, "TrAId": 0.10}
    line = m.group(0).split('—', 1)[-1]
    parts = [p.strip() for p in line.split('|')]
    mapping: Dict[str, float] = {}
    name_map = {"Mirror": "VoiceMirror"}
    for part in parts:
        if not part:
            continue
        name, pct = part.split()[:2]
        key = name_map.get(name, name)
        mapping[key] = float(pct.strip('%')) / 100.0
    return mapping


def resurrect() -> Dict[str, Any]:
    """Reload anchors from disk (resurrection protocol)."""
    return load_all()
