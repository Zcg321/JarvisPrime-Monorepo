"""Voice Mirror clarity helper.

This module reflects the user's text back with a gentle nudge toward
action.  It also searches Continuum philosophies for a matching keyword
and appends the first snippet that aligns with the user's words.
"""

import re

from src.core import anchors

PHILOSOPHIES = anchors.load_all()["master"]["manifest"]["philosophies"]

# Affect prompts gently bias the reflection tone. Only four states are
# supported to keep the helper deterministic.
AFFECT_PROMPTS = {
    "calm": "What is the smallest next true step you can finish in 20 minutes?",
    "anxious": "Take a deep breath; what small step will ease your mind?",
    "confident": "Leverage your momentum; what's the next true step?",
    "frustrated": "Pivot gently; what's one step that keeps progress honest?",
}


def _find_snippet(text: str) -> str:
    """Return philosophy snippet whose keywords appear in ``text``.

    The search is case-insensitive and scans both philosophy titles and
    their descriptions.  The first match is returned.
    """

    low = text.lower()
    # First check philosophy titles for direct keyword matches.
    for title, line in PHILOSOPHIES.items():
        tokens = re.findall(r"\w+", title.lower())
        if any(tok in low for tok in tokens):
            return line

    # Fallback: scan philosophy descriptions.
    for line in PHILOSOPHIES.values():
        tokens = re.findall(r"\w+", line.lower())
        if any(tok in low for tok in tokens):
            return line

    return ""


def reflect(text: str, affect: str = "calm") -> str:
    """Return clarity statement optionally grounded in a philosophy.

    ``affect`` adjusts the guidance wording for the user. Unknown states fall
    back to ``calm``.
    """

    text = text.strip()
    snippet = _find_snippet(text)
    prompt = AFFECT_PROMPTS.get(affect, AFFECT_PROMPTS["calm"])
    base = f"Clarity: {text}. {prompt}"
    if snippet:
        base = f"{base} {snippet}"
    return base
