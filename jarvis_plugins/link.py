from __future__ import annotations

import os
from typing import Any, Dict

import httpx

TARGETS = {
    "openai": ("OPENAI_API_URL", "OPENAI_API_KEY"),
    "grok": ("GROK_API_URL", "GROK_API_KEY"),
    # add more targets via environment variables as needed
}


def call_ai(target: str, prompt: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Call an external AI service.

    Parameters
    ----------
    target: str
        The key name of the external AI (e.g., "openai", "grok").
    prompt: str
        User prompt to send.
    params: Dict[str, Any] | None
        Additional JSON parameters.

    Environment variables provide the API URL and key for each target.
    For example ``OPENAI_API_URL`` and ``OPENAI_API_KEY``.
    """
    if target not in TARGETS:
        raise ValueError(f"Unknown target: {target}")

    url_env, key_env = TARGETS[target]
    url = os.getenv(url_env)
    key = os.getenv(key_env)
    if not url or not key:
        raise RuntimeError(f"Missing credentials for {target}")

    payload: Dict[str, Any] = {"prompt": prompt}
    if params:
        payload.update(params)
    headers = {"Authorization": f"Bearer {key}"}

    resp = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    resp.raise_for_status()
    return resp.json()
