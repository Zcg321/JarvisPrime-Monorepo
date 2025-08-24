#!/usr/bin/env bash
set -euo pipefail
if [ $# -lt 1 ]; then
  echo "usage: $0 <archive.tar.gz> [--force]" >&2
  exit 1
fi
ARCH=$1
FORCE=${2:-}
TMP=$(mktemp -d)
tar -xzf "$ARCH" -C "$TMP"
for f in alchohalt.db logs/alchohalt.jsonl .env.example; do
  [ -e "$TMP/$f" ] || continue
  if [ -e "$f" ] && [ "$FORCE" != "--force" ]; then
    echo "$f exists; use --force to overwrite" >&2
    continue
  fi
  mkdir -p "$(dirname "$f")"
  cp "$TMP/$f" "$f"
done
echo "restored from $ARCH"
