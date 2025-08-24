from __future__ import annotations

import json
import re
from typing import Any, Tuple


class JSONGuard:
    """
    Validates that a tool reply is strict JSON. Provides helpful error messages.
    """

    codeblock_pat = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)

    @classmethod
    def extract_and_validate(cls, text: str) -> Tuple[dict, str]:
        """
        Attempt to parse JSON from text. Prefer fenced JSON; fallback to first {...}.
        Returns (parsed_dict, mode) where mode is 'fenced' or 'raw'.
        Raises ValueError on failure.
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string.")
        m = cls.codeblock_pat.search(text)
        if m:
            candidate = m.group(1)
            try:
                return json.loads(candidate), "fenced"
            except Exception as e:
                raise ValueError(f"Invalid fenced JSON: {e}")

        # Fallback: first balanced-ish object (cheap heuristic)
        brace = text.find("{")
        last = text.rfind("}")
        if brace != -1 and last != -1 and last > brace:
            candidate = text[brace:last + 1]
            try:
                data = json.loads(candidate)
                if not isinstance(data, dict):
                    raise ValueError("JSON root must be an object.")
                return data, "raw"
            except Exception as e:
                raise ValueError(f"Invalid JSON: {e}")

        raise ValueError("No JSON object found.")
