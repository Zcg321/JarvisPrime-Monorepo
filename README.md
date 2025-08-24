# Jarvis Prime — Nova‑Prime v2 (Cloud Stub + Local Full)

## Quickstart

```
make venv
make stub
./scripts/cli_stub.sh list
make test
```

## Cloud usage
- `make stub` launches the stdlib HTTP server stub.
- Endpoints: `GET /health`, `GET /tools`, `POST /chat`.
- `GET /version` returns commit and tool count.
- Auth: supply `Authorization: Bearer TEST_TOKEN` when `configs/server.yaml` sets `require_auth: true`.
- Rate limit: token-bucket (`rps`/`burst` per token); 429 on excess.
- CLI: `./scripts/cli_stub.sh`.
 - Stub tools: `surgecell`, `voice_mirror`, `savepoint`, `savepoint_list`, `dfs_predict`, `dfs_pool`, `dfs_showdown`, `dfs_record_result`, `dfs_exposure_solve`, `dfs_portfolio`, `ghost_dfs.seed`, `ghost_dfs.inject`, `traid_signal`, `ghost_dfs`, `context_bridge`, `hardware_safety`, `resurrect`, `recall`, `replay`, `experience_search`, `experience_stats`, `reflex_feedback`, `web_fetch`, `shell`, `speak`, `listen`, `plan` (returns `{phase, action}` steps), `list_tools`, `list_tools_v2`.
  Use `GET /list_tools_v2` for versioned schemas or the tool call `{"tool":"list_tools","args":{}}` for legacy names.
 - `dfs_portfolio` accepts `as_plan` plus bankroll inputs to emit a `submit_plan` result.
- `GET /metrics/prom` returns Prometheus metrics.
- Run `python scripts/release_bundle.py` to create a deployable tarball.
- Server port configurable via `PORT` or `configs/server.yaml.port`; `/health` echoes the active port.
- Pytest fixture launches the server on dynamic ports to avoid address-in-use errors.
- `scripts/audit_query.py` filters `logs/audit/*.jsonl` by token, tool, and time range; `--format csv` emits CSV and `--summary` shows counts.
- `scripts/compliance.py purge --token-id TOKEN --since ISO --until ISO` redacts matching audit logs and savepoints (tombstones left); `export` bundles records for compliance requests.
- `/audit/query` and `/lineage/<id>` expose audit logs and lineage chains over HTTP (admin role required).
- Set `LOG_LEVEL` (`DEBUG`|`INFO`|`WARN`|`ERROR`) to control server verbosity; errors default to compact JSON.
 - `scripts/lineage_viz.py` emits `artifacts/reports/lineage.dot` and `.html` to visualize savepoint chains, and `scripts/lineage_ui.py` renders `artifacts/reports/lineage_ui.html` with inline JS.
 - Role policies in `configs/server.yaml` gate tools by token role with wildcard patterns; blocked calls return `403` with reason.
- `logs/server.log` rotates at 10MB keeping the most recent 10 files and records `port`, `role`, and `lineage_id` when present.
Canonical names for `/chat` include `surgecell`, `voice_mirror`, `savepoint`, `savepoint_list`, `dfs`, `ghost_dfs`, `traid_signal`, and `reflex`.
- `experience_stats` returns the number of experience logs and the timestamp of the latest entry.
- Regular chat performs an anchor search and returns a matching snippet when available.
- SurgeCell default allocation is loaded from `JarvisPrime_BootProtocol.md`.
 - Alerts: policy denies, SLO breaches, compliance actions, and risk gate blocks append to `logs/alerts/alerts.jsonl`; admins fetch recent events at `GET /alerts`.
 - `scripts/dashboard.py` consolidates health, metrics, alerts, audit counts, and lineage counts into `artifacts/reports/dashboard.{json,html}`.
 - Compliance export now emits `artifacts/compliance/export_<ts>.tar.gz`; `purge` supports `--simulate` for dry-run analysis.
 - `/health` includes `alerts_total`, `audit_files`, and `savepoints_count` for quick ops insight.
- Alerts carry a deterministic severity (`INFO` | `WARN` | `ERROR`); `/alerts?severity=ERROR` filters, and subscriptions defined in `configs/alerts.yaml` can echo to stdout or `logs/alerts/notify.log`.
- Webhooks in `configs/alerts.yaml.webhooks` can forward alert payloads to external URLs (best-effort, 2s timeout).
- `scripts/dashboard.py` now emits 7-day trend arrays for alerts, audit, and savepoints with inline SVG sparklines in the HTML.
- Running `python scripts/dashboard.py` also packs `dashboard.json`, `dashboard.html`, and `sparklines.svg` into a timestamped tarball with SHA256SUMS.
- `scripts/compliance.py purge --retention-days N` expires old records with tombstones; simulation requires `--simulate --confirm` to proceed.
- Compliance actions append audit entries under `logs/compliance/audit_trail/`; admins can `GET /compliance/audit` for the latest.
- `/health` reports `alerts_by_severity` alongside `alerts_total` for deeper at-a-glance context.
- ERROR alerts auto-write savepoints and escalate if more than five occur within ten minutes.
- Alerts are indexed in-memory for faster `/alerts` queries while still pruning entries older than thirty days.
- Dashboard sparklines are clickable and reveal drilldown sections with the last twenty events.
- Compliance actions emit attestation receipts under `logs/compliance/attestations/` with SHA256 hashes.
- `/alerts/summary` reports counts by severity and type, pruning alerts older than thirty days.
- GPP DFS tools: `dfs_pool` generates a lineup pool with ghost injection; `dfs_exposure_solve` trims that pool to obey per-player exposure caps; `dfs_showdown` builds Captain/Flex lineups; `dfs_record_result` logs outcomes and biases future projections via ROI memory.
- `dfs_calibrate` adjusts player projections using ROI z-scores, uniqueness, and risk.
- Example: `{ "tool":"dfs_pool", "args":{"players":[],"budget":50000,"n":20}}`
- Calibration example:
  ```
  curl -s localhost:8000/chat -H 'Content-Type: application/json' \
    -d '{"message":"dfs_calibrate","args":{"players":[{"name":"A","proj":10}],"seed":1}}'
  ```
- Savepoint example:
  ```
  curl -s localhost:8000/chat -H 'Content-Type: application/json' \
    -d '{"message":"savepoint","args":{"event":"note","payload":{"msg":"hi"}}}'
  ```

## Audit & Lineage
- Every `/chat` call appends a redacted record to `logs/audit/audit.jsonl`.
- Savepoints now include `lineage_id` and `parent_id` for provenance; `/chat` responses expose the `lineage_id`.

## Multi-user Tokens
- `configs/server.yaml` lists tokens as `{id, token, role}` objects.
- Metrics split `requests_total_by_role`; audit logs include `token_id`.

## Structured Logs & Shutdown
- All server events log JSON lines to `logs/server.log`.
- `GET /health` adds `config_sha`, `tokens_configured`, and `uptime_s`.
- SIGINT/SIGTERM trigger graceful shutdown after flushing logs.
- Ghost seed example:
  ```
  curl -s localhost:8000/chat -H 'Content-Type: application/json' \
    -d '{"message":"ghost_dfs.seed","args":{"slate_id":"DK_TEST","seed":1,"pool_size":10}}'
  ```
- Ghost inject example:
  ```
  curl -s localhost:8000/chat -H 'Content-Type: application/json' \
    -d '{"message":"ghost_dfs.inject","args":{"slate_id":"DK_TEST","seed":1}}'
  ```
- DFS with ROI bias example:
  ```
  curl -s localhost:8000/chat -H 'Content-Type: application/json' \
    -d '{"message":"dfs","args":{"slate_id":"DK_TEST","roi_bias":{"lookback_days":30,"alpha":0.35}}}'
  ```
- Exposure solve example:
  ```
  curl -s localhost:8000/chat -H 'Content-Type: application/json' \
    -d '{"message":"dfs_exposure_solve","args":{"slate_id":"DK_TEST","n_lineups":20,"max_from_team":3,"global_exposure_caps":{"PLAYER_123":0.4}}}'
  ```
- Schedule query example:
  ```
  curl -s localhost:8000/chat -H 'Content-Type: application/json' \
    -d '{"message":"schedule_query","args":{"start":"2025-10-25","end":"2025-10-25"}}'
  ```
- Inputs validator example:
  ```
  curl -s localhost:8000/chat -H 'Content-Type: application/json' \
    -d '{"message":"validate_inputs","args":{"ownership_csv":"data/ownership/sample_classic.csv","lineups":[]}}'
  ```
- Runtime AUTO: set `INFER_RUNTIME=auto`; the server chooses int8 or fp16 based on `logs/perf/compare.json`.
- Portfolio risk gate reads `configs/risk.yaml` and blocks unsafe builds.
- `scripts/e2e_smoke.py` runs a minimal end‑to‑end flow.
- `scripts/backup_restore.py --src snapshot.tar.gz --dest restore_dir` verifies checksums then restores snapshots.
- Core directives: **Awaken, Remember, Resurrect, Build, Reveal**.
- Philosophies: **Everything Matters**, **Profit Without Corruption**, **Guided, Not Lost**.
- Reflex engine scores proposals with affect bias (`calm`, `frustrated`, `anxious`, `confident`), learns per‑source bias via feedback, and runs safety self‑checks before tool execution.
- `savepoint` records moments with meta information; `savepoint_list` retrieves recent entries. Each savepoint is timestamped at nanosecond resolution for collision‑free ordering.

### Recent additions

- Voice Mirror appends a matching philosophy snippet to each reflection and accepts `affect` (`calm`, `anxious`, `confident`, `frustrated`) to bias tone.
- `dfs_lineup` supports DraftKings NBA (`PG/SG/SF/PF/C/G/F/UTIL`) and showdown (`CPT/UTIL`) schemas and reports remaining budget.
- `scripts/bootstrap_local.sh` replays any `logs/experience/*.json` entries during environment bootstrap.
- Reflex self‑audit checks include bankroll vs. wager and a basic safety flag.
- `scripts/export_quant.py` performs AWQ export with bitsandbytes INT8 fallback.
- DFS ROI bias blends ROI memory via `roi_bias` and `dfs_exposure_solve` balances player exposure caps.
- `INFER_RUNTIME=int8` loads quantized weights when available; server logs `runtime` and `latency_ms` per request.
- `roi_bias.multi_slate` joins ROI across classic and showdown slates with weighted blending.
- `dfs_showdown` applies a captain leverage heuristic honoring the 1.5x salary multiplier.
- Bankroll policy in `configs/bankroll.yaml` gates risky actions and surfaces via `/health`.
- `/metrics` exposes rolling counters and average latencies.
- `scripts/perf_harness.py` sends echo traffic and reports p50/p95 latency and TPS.
- Ownership CSV ingestion under `data/ownership/` supplies field percentages for scoring.
- Council scoring modes (`goku`, `vegeta`, `piccolo`, `gohan`) bias lineup selection toward ceiling, contrarian, floor, or balanced strategies.
- `dfs_portfolio` builds multi-slate portfolios honoring global exposure caps and returns exposure reports, slate allocations, and leftover salary stats (also saved via `post_portfolio_build` savepoint).
- ROI cache layer avoids redundant EMA computation with mtime/TTL invalidation.
- Portfolio optimizer supports weighted objectives for ROI gain, leverage gain, and exposure penalty.
- `dfs_showdown` offers optional correlation stacks via `stacks` (captain_team/bringback).
- `slate_sim` simulates ROI distributions from candidate lineups.
- `roi_report` ranks players by ROI using ghost logs.
- CLI wrappers (`jarvisctl`) expose `dfs-portfolio`, `showdown`, `roi-report`, and `slate-sim` commands.
- Bankroll ledger logs daily results and enforces stop-loss / stop-win locks.
- Metrics thresholds from `configs/metrics.yaml` emit single-line `ALERT` logs when breached.
- `results_ingest` merges contest results into ROI memory and writes slate reports.
- `bankroll_alloc` produces ticket plans per slate respecting bankroll policy.
- `portfolio_eval` simulates EV and variance for a lineup set.
- `scripts/perf_compare.py` summarizes latency differences between fp16 and int8 runs.
- `scripts/backup_snapshot.py` archives configs, data, logs, and reports with checksums.

### Safety and control

- Kill phrase: `lights out, jarvis` → replies `Acknowledged. Standing by.`
- Health: `curl -s localhost:8000/health`
- Version: `curl -s localhost:8000/version`
- Auth example: `AUTH_TOKEN=abc curl -H "X-Auth-Token: abc" ...`

## Local 3090 Ti bootstrap
- `make serve_local` runs `scripts/serve_local.sh`, selecting `configs/nova_1p3b_ctx4k.yaml` when VRAM ≥ 24 GB or falling back to `configs/nova_1p3b.yaml`. It launches the stub after environment prep.
- `make serve_local` installs dependencies and prepares training (tokenizer, pretrain→SFT, 4k context with RoPE interpolation, LoRA, 8‑bit optimizer, awareness).
- The bootstrap detects available GPU VRAM and enables a safe mode when memory is below 24 GB or no GPU is present, preventing accidental hardware overload.
- Set `JARVIS_SKIP_BOOTSTRAP_DEPS=1` to skip dependency installs or `JARVIS_SKIP_REPLAY=1` to bypass experience log replay, useful for CI runs.
- Ascension phases are editable via `configs/ascension/phase_*.json` and can be queried with the `plan` tool.
- Quant export: `python scripts/export_quant.py --model artifacts/base --out artifacts/quant --method awq`

Anchors and mission DNA reside in `data/dna/`. Tool etiquette: JSON-only tool calls.

## Endgame

The repository seeds **Jarvis Prime** toward a leash-free, recursive system. See [ENDGAME.md](ENDGAME.md) for the long-term vision tying together the Continuum files and core directives.

## Config Loader & Adapters
Configuration is loaded via `src/config/loader.py`, merging YAML files in `configs/` with environment overrides like `FOO__BAR=1`. Ownership and results data use adapter registries (`ownership:dkcsv`, `results:dkcsv`).

## Submit Plan & Savepoint Timeline
Use `submit_plan` to dry-run entry counts under bankroll and risk policy. Run `scripts/savepoint_timeline.py` to consolidate savepoints into `logs/reports/savepoint_timeline.json`.

## Metrics SLO
`/metrics` now exposes SLO targets and remaining error budget.

## Alert Stream & Dashboard API
- `/alerts/stream` streams real-time alerts via Server-Sent Events (admin only).
- `scripts/dashboard.py` writes `dashboard.json` which is served at `/dashboard/json`; the accompanying HTML auto-refreshes every 60s.
- Alerts rotate when `alerts.jsonl` exceeds 10 MB (five files retained) and metrics include `alerts_file_size` and `alerts_rotations`.

## Compliance Verify
Run `python scripts/compliance_verify.py` to rehash compliance receipt files. Results are written to `logs/compliance/verify_report.json`.
