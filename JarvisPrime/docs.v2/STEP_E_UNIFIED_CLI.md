# Step E — Unified CLI

## New tool: `python -m jarvis_plugins.unified_cli`
Supports:
- `save` : create savepoint
- `recent` : list recent savepoints
- `reflect <text>` : voice mirror anchor
- `export-int8` : guarded INT8 export

Makefile targets:
- `make cli-unified` (help)
- `make cli-export-int8` (run export)

Torch guard ensures safe behavior with or without torch installed.
