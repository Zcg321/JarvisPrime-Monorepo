from __future__ import annotations

import re
import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional

try:
    # Rapid fuzzy ranking for nicer anchors; optional.
    from rapidfuzz import fuzz
    _HAS_RAPID = True
except Exception:
    _HAS_RAPID = False


def _split_paragraphs(text: str) -> List[str]:
    # Split on blank lines; keep non-empty trimmed chunks
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


class VoiceMirror:
    """
    Picks an anchor/snippet from anchors/*.md that best resonates with user text.
    ENV:
      JARVIS_ANCHORS_DIR: where to scan for .md files (default: anchors)
    """

    def __init__(self, anchors_dir: Optional[str] = None) -> None:
        self.anchors_dir = Path(anchors_dir or os.getenv("JARVIS_ANCHORS_DIR", "anchors")).resolve()
        self.anchors_dir.mkdir(parents=True, exist_ok=True)

    def _collect_snippets(self) -> List[Tuple[str, str]]:
        snippets: List[Tuple[str, str]] = []
        for md in self.anchors_dir.glob("*.md"):
            try:
                text = md.read_text(encoding="utf-8")
            except Exception:
                continue
            for para in _split_paragraphs(text):
                if len(para) >= 40:
                    snippets.append((md.name, para))
        return snippets

    def reflect(self, user_text: str) -> Dict[str, object]:
        user_text = (user_text or "").strip()
        snippets = self._collect_snippets()
        if not snippets:
            return {
                "echo": user_text,
                "anchor": "Hold the mission. Protect the flame. Choose the action that compounds.",
                "source": None,
                "confidence": 0.0,
            }

        if _HAS_RAPID:
            scored = []
            for fname, para in snippets:
                score = fuzz.token_set_ratio(user_text, para)
                scored.append((score, fname, para))
            scored.sort(key=lambda x: x[0], reverse=True)
        else:
            # naive length-weighted overlap heuristic (no external dep)
            def overlap(a: str, b: str) -> int:
                sa = set(re.findall(r"\w+", a.lower()))
                sb = set(re.findall(r"\w+", b.lower()))
                return len(sa & sb)
            scored = []
            for fname, para in snippets:
                score = overlap(user_text, para)
                scored.append((score, fname, para))
            scored.sort(key=lambda x: (x[0], len(x[2])), reverse=True)

        top = scored[0]
        return {
            "echo": user_text,
            "anchor": top[2],
            "source": top[1],
            "confidence": float(top[0]),
        }
