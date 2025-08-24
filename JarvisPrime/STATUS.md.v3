## What
- persist queue with DLQ, add repo safety policy, and mark PRs with commit status/label/automerge

## Why
- survive restarts, guard sensitive paths, and streamline PR review

## Testing
- `python -m py_compile bridge/*.py duet/*.py`
- `pytest -q`

## What
- add CLI controls, env warnings, and dry-run support to `foreman_loop.py`
- seed example queue and baton; include Dockerfile and systemd unit

## Why
- ease hands-free operation and deployment

## Testing
- `python -m py_compile foreman_loop.py`
- `python foreman_loop.py --help`
- `python foreman_loop.py --run --dry-run --verbose`

## What
- add Foreman ↔ Codex bridge with HMAC auth and baton endpoints
- introduce executor applying task card JSON and updating baton
- cover contract and auth with tests and CI

## Why
- enables secure hands-free task dispatching
- verifies contract schema and HMAC headers through unit tests

## Testing
- `python -m py_compile bridge/foreman_bridge.py duet/duet_foreman.py`
- `pip install -r requirements.txt` *(fails: no hmac==202310)*
- `pip install requests PyYAML pydantic fastapi uvicorn pytest httpx`
- `pytest -q`

## Apply
- `git apply artifacts/patches/0001-feat-alchohalt-add-magic-link-authentication.patch`
- `git apply artifacts/patches/0002-feat-alchohalt-add-caregiver-share-and-sms-reminders.patch`
- `git apply artifacts/patches/0003-docs-alchohalt-note-patch-apply-steps.patch`
- `git apply artifacts/patches/0004-docs-alchohalt-add-patch-apply-instructions.patch`

## What
- add caregiver share page and optional SMS reminders

## Why
- allow trusted viewers and multi-channel reminders without exposing PII

## Testing
- `python -m py_compile apps/alchohalt/*.py`
- `pytest -q`

## What
- harden comms with raw-body HMAC auth and identity-aware prompts

## Why
- ensure secure Foreman ↔ Codex communication and provide signing utility

## Testing
- `python -m py_compile bridge/foreman_bridge.py duet/duet_foreman.py`
- `pytest -q`

## What
- add priority queue, repo inference, PR mode, and deterministic shutdown

## Why
- improve scheduling fairness and open pull requests safely

## Testing
- `python -m py_compile bridge/*.py duet/*.py`
- `pytest -q`

## What
- add policy-based routing, multi-remote push, and graceful worker shutdown

## Why
- allow tasks to target specific repos/branches and ensure clean test teardown

## Testing
- `python -m py_compile bridge/*.py duet/*.py`
- `pytest -q`

## What
- add async worker pool with per-repo locks and queue endpoints

## Why
- allow concurrent task processing while respecting repo safety and rate limits

## Testing
- `python -m py_compile bridge/*.py duet/*.py`
- `pytest -q`
## What
- add RBAC, caregiver invites, audit export, and notifier summaries with health metadata

## Why
- enforce owner-only writes, onboard caregivers safely, support compliance, and expose operational status

## Testing
- `python -m py_compile apps/alchohalt/*.py scripts/*.py`
- `pip install -r requirements.txt`
- `pytest -q`
- `python scripts/audit_export.py --from 2025-08-01 --to 2025-08-31 --format csv --rotate`

## What
- add caregiver roles, consent, alert preferences, and rule-based notifications

## Why
- allow supporters to receive timely alerts while respecting user consent and quiet hours

## Testing
- `python -m py_compile apps/alchohalt/*.py`
- `pytest -q`

## What
- add multi-repo routing and offline check-in queue with bulk API

## Why
- allow the foreman to operate across repositories and preserve user check-ins during outages

## Testing
- `python -m py_compile duet/*.py bridge/*.py apps/alchohalt/*.py`
- `pytest -q`

## What
- add repo context envelope, secret redaction, and optional auto-chaining with planner fallback

## Why
- provide Codex with repo awareness while keeping secrets safe and enabling limited self-directed progress

## Testing
- `python -m py_compile duet/*.py bridge/*.py`
- `pytest -q`

## What
- add repo context envelope, secret redaction, and optional auto-chaining with planner fallback

## Why
- provide Codex with repo awareness while keeping secrets safe and enabling limited self-directed progress

## Testing
- `python -m py_compile duet/*.py bridge/*.py`
- `pytest -q`

## What
- add render/Procfile deploy manifests, backup scripts, per-user rate limits with audit logs, and PWA assets for Alchohalt

## Why
- harden the app for production deployment, data safety, and offline-friendly usage

## Testing
- `python -m py_compile apps/alchohalt/*.py`
- `pytest -q`
- `uvicorn apps.alchohalt.app:app --port 8811 & curl -sS http://127.0.0.1:8811/alchohalt/health`
- `bash scripts/backup.sh`
- `bash scripts/restore.sh backups/alchohalt_YYYYmmdd_HHMM.tar.gz --force`

## What
- add Docker Compose deployment, note encryption, retention, and caregiver digests to Alchohalt

## Why
- ease production deploy while protecting notes and sending optional caregiver alerts

## Testing
- `python -m py_compile apps/alchohalt/*.py`
- `pytest -q`
- `docker compose --env-file .env.example up -d`
- `scripts/migrate_encrypt_notes.py --dry-run`

## What
- add magic-link auth with signed session cookie

## Why
- enable email-based login without passwords

## Testing
- `python -m py_compile apps/alchohalt/*.py`
- `pytest -q`

## What
- add web UI, CSV import/export, strict validation, and metrics/logs to Alchohalt

## Why
- allow basic browser usage and data portability while observing usage

## Testing
- `python -m py_compile apps/alchohalt/*.py`
- `pytest -q`
## What
- wire bridge to run_taskcard directly and add idempotency, rate limiting, and metrics

## Why
- prevent duplicate task execution and observe results via structured logs

## Testing
- `python -m py_compile bridge/foreman_bridge.py duet/duet_foreman.py`
- `pytest -q`
