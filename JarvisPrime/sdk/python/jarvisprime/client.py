from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List
from urllib import request, error


class JarvisPrime:
    def __init__(self, token: str | None = None, base_url: str | None = None) -> None:
        self.token = token or os.environ.get("JARVIS_TOKEN", "")
        if base_url:
            self.base = base_url.rstrip("/")
        else:
            env = os.environ.get("JARVIS_BASE_URL")
            if env:
                self.base = env.rstrip("/")
            else:
                self.base = self._discover().rstrip("/")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def _discover(self) -> str:
        for port in range(8000, 8011):
            url = f"http://127.0.0.1:{port}/health"
            try:
                with request.urlopen(url, timeout=0.2):
                    return f"http://127.0.0.1:{port}"
            except Exception:
                continue
        return "http://127.0.0.1:8000"

    def _req(self, method: str, path: str, body: dict | None = None) -> dict:
        url = self.base + path
        data = json.dumps(body or {}).encode() if body is not None else None
        req = request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        if body is not None:
            req.add_header("Content-Type", "application/json")
        for i in range(3):
            try:
                with request.urlopen(req) as resp:
                    return json.loads(resp.read().decode())
            except error.HTTPError as e:
                if 500 <= e.code < 600 and i < 2:
                    time.sleep(0.25 * (2 ** i))
                    continue
                raise
            except Exception:
                if i < 2:
                    time.sleep(0.25 * (2 ** i))
                    continue
                raise

    def chat(self, message: str, args: dict | None = None) -> dict:
        return self._req("POST", "/chat", {"message": message, "args": args or {}})

    def health(self) -> dict:
        return self._req("GET", "/health")

    def admin_get(self, path: str) -> dict:
        return self._req("GET", path)

    def metrics(self) -> dict:
        return self.admin_get("/metrics")

    def list_tools(self) -> dict:
        return self.admin_get("/list_tools_v2")

    def stream_alerts(self, max_seconds: float = 10.0):
        url = self.base + "/alerts/stream"
        req = request.Request(url)
        req.add_header("Authorization", f"Bearer {self.token}")
        start = time.time()
        while time.time() - start < max_seconds:
            try:
                with request.urlopen(req, timeout=max_seconds) as resp:
                    for line in resp:
                        if line.startswith(b"data:"):
                            data = line.split(b":", 1)[1].strip()
                            if data:
                                try:
                                    yield json.loads(data)
                                except Exception:
                                    yield None
                    break
            except Exception:
                time.sleep(0.25)

    def chat_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for it in items:
            try:
                res = self.chat(it.get("message", ""), it.get("args"))
                out.append({"ok": True, "response": res})
            except Exception as e:
                out.append({"ok": False, "error": str(e)})
        return out


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("token")
    parser.add_argument("message")
    args = parser.parse_args()
    client = JarvisPrime(args.token)
    print(client.chat(args.message))


if __name__ == "__main__":  # pragma: no cover
    main()
