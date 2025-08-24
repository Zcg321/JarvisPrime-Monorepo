import shlex
import subprocess
import urllib.request
from typing import Optional

ALLOWED_CMDS = {"echo", "ls", "pwd", "cat"}


def web_fetch(url: str, max_chars: int = 1000) -> str:
    """Fetch text content from a URL (up to ``max_chars``)."""
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            text = r.read().decode(errors="replace")
        return text[:max_chars]
    except Exception as exc:  # pragma: no cover - error path
        return f"error: {exc}"[:max_chars]


def shell(cmd: str) -> str:
    """Run a whitelisted shell command and return stdout."""
    parts = shlex.split(cmd)
    if not parts or parts[0] not in ALLOWED_CMDS:
        raise ValueError("command not allowed")
    out = subprocess.run(parts, capture_output=True, text=True)
    return out.stdout.strip()


def speak(text: str) -> str:
    """Stub text-to-speech; returns text that would be spoken."""
    return f"speaking: {text}"


def listen(prompt: Optional[str] = None) -> str:
    """Stub speech recognition; echoes prompt as heard."""
    return f"heard: {prompt or ''}"
