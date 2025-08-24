#!/usr/bin/env bash
set -euo pipefail
mkdir -p backups
TS=$(date +%Y%m%d_%H%M)
DEST="backups/alchohalt_${TS}.tar.gz"
tar -czf "$DEST" --ignore-failed-read alchohalt.db logs/alchohalt.jsonl .env.example
echo "created $DEST"
