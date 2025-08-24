# Status

## Alchohalt MVP shipped
- Added `alchohalt.checkin`, `alchohalt.metrics`, and `alchohalt.schedule` tools.
- Stores entries in `data/alchohalt.db` and computes streak metrics.

## Usage
- Set reminder time via `/chat` with `{ "tool":"alchohalt.schedule", "args":{"hour":21,"minute":0} }`.
- Record a check-in: `{ "tool":"alchohalt.checkin", "args":{"status":"halted"} }`.
- Fetch metrics: `{ "tool":"alchohalt.metrics", "args":{} }`.

## Testing
- `pytest -q`

## vNext+26.hotfix
- Restored flag defaults and flip semantics; legacy tokens allowed under global risk with WARN savepoints.
- Ghost DFS reads legacy ROI logs and mirrors writes when `ROI_LOG_COMPAT_MIRROR=1`.
- Cohort drift detection uses deterministic windows and emits single WARN per cohort.
- Metrics rollups log 4xx reasons; SDK client adds context manager and auto `/health` discovery.

## vNext+29.hotfix
- `submit_plan` uses a strict schema and logs `post_submit_plan` with lineup ids and sim summary.
- Dry-run tools bypass risk gates (logged as WARN) while explicit policies still deny acting tools.
- Savepoints track per-token parent pointers under `logs/savepoints/<token>/__last/`.
- DK export checker allows empty files and bundle manifest records generator, slate, checksum, and count.
- Metrics rollups now include 4xx reason counts without skewing latency percentiles.

## Next
- Add notification nudges and dashboard integration.
