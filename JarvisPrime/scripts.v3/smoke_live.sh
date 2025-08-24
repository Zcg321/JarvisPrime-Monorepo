#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${FOREMAN_SHARED_TOKEN:-}" ]]; then
  echo "FOREMAN_SHARED_TOKEN not set" >&2
  exit 1
fi
BODY='{"task_card":"Add LICENSE (MIT) and README badge"}'
SIG=$(python scripts/sign_taskcard.py "$BODY")
curl -sS http://localhost:8787/v1/health | jq .
curl -sS -X POST http://localhost:8787/v1/taskcards \
  -H "Content-Type: application/json" \
  -H "X-Foreman-Id: jarvis-foreman" \
  -H "X-Foreman-Conv: continuum-foreman-thread" \
  -H "X-Foreman-Sign: $SIG" \
  -H "X-Idempotency-Key: smoke-001" \
  -d "$BODY" | jq .
curl -sS http://localhost:8787/v1/baton | jq .
curl -sS http://localhost:8787/v1/metrics | jq .
