#!/usr/bin/env bash
set -euo pipefail
CFG="configs/nova_1p3b.yaml"
if command -v nvidia-smi >/dev/null 2>&1; then
    MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
    if [ "$MEM" -ge 24000 ]; then
        CFG="configs/nova_1p3b_ctx4k.yaml"
    fi
fi
echo "Using config $CFG"
python -m src.serve.server_stub
