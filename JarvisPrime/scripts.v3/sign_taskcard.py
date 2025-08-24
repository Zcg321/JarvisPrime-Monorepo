#!/usr/bin/env python3
"""Compute HMAC-SHA256 signature for a Task Card body."""
import hmac
import hashlib
import os
import sys


def sign(body: str, token: str) -> str:
    return hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python scripts/sign_taskcard.py '<raw-json-body>'", file=sys.stderr)
        sys.exit(1)
    token = os.getenv("FOREMAN_SHARED_TOKEN")
    if not token:
        print("FOREMAN_SHARED_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    body = sys.argv[1]
    print(sign(body, token))


if __name__ == "__main__":
    main()
