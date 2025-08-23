# Step F — DNA Auto-Sync, Schema Contracts, Persistence Daemon, CI

## DNA Auto-Sync
- Set `JARVIS_DNA_AUTOSYNC=1` to append every savepoint payload into the RAG JSON index automatically.
- `POST /plugins/rag/rebuild` rebuilds the index from anchors and savepoints.
- Produces `artifacts/rag/index.json` always; when available, also creates FAISS+embeddings.

## Schema Contracts
- `POST /plugins/tools/validate_contract` with `{"text": "<json>", "schema":"ToolReply"}` enforces structure via pydantic.
- Extend in `jarvis_plugins/contracts.py`.

## Persistence Daemon
- Enable with `JARVIS_DAEMON_ENABLE=1` (interval via `JARVIS_DAEMON_INTERVAL` seconds).
- Writes periodic heartbeat savepoints with tag `daemon`.

## CI Consolidation
- `make ci` runs all core tests including contracts, autosync, crash, JSON guards, plugins.
- `make rag-rebuild` triggers a rebuild locally.
