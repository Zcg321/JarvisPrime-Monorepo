# Jarvis Prime Desktop

Jarvis Prime Desktop is a fully autonomous, OS-level AI assistant designed to operate as a true user on your machine — indistinguishable from human interaction. It serves as the sensory and control layer for Jarvis Prime, acting as its **eyes, ears, hands, and feet**.

> **Who is who**
> - This ChatGPT thread is the **Foreman (Jarvis)**.
> - The code in this repo runs the **Codex executor**.
> - They communicate via the bridge API using HMAC-signed headers.

## Features
- Direct OS-level interaction without browser automation tools like Selenium or Playwright
- Simulates a real human user to bypass bot detection
- Integrates with local and network resources
- Modular design for expansion into any workflow or application
- Built for seamless integration into the larger Jarvis Prime ecosystem

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/zcg3214/JarvisPrimeDesktop.git
   cd JarvisPrimeDesktop
   ```
2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Export required environment variables:
   ```bash
   export OPENAI_API_KEY=sk-...
   export GT_TOKEN=ghp_...
   # optional
   export CODEX_MODEL=gpt-5-codex
   export OPENAI_BASE_URL=https://api.openai.com/v1
   ```

## Foreman Loop

`foreman_loop.py` provides a hands-free automation loop that sends tasks to Codex via the OpenAI API, commits/pushes changes, records status, and advances through a queue.

### CLI

```bash
python foreman_loop.py --init           # create foreman/, artifacts/, logs/
python foreman_loop.py --seed-example   # seed example queue
python foreman_loop.py --status         # print baton.json
python foreman_loop.py --run --dry-run  # generate prompt without API/push
python foreman_loop.py --watch --interval 120
```

`foreman_loop.py --help` lists all available options. The loop writes state to `foreman/`, outputs to `artifacts/`, and logs to `logs/foreman.log`.

### How Codex sees your repo
Before each run the executor compiles a **Context Envelope** containing a file map, hot-file excerpts, recent commits, last diff, baton excerpt, anchors, and the Task Card. The envelope size (in bytes) is recorded in `foreman/baton.json` as `context_bytes`.

### Secrets and logs
The executor redacts values for keys such as `OPENAI_API_KEY`, `GT_TOKEN`, `ALC_*`, `TWILIO_*`, and `FOREMAN_SHARED_TOKEN` before writing to artifacts or logs. Keep secrets out of committed files and `.env` is never scanned.

### Auto-chain vs Planner
Set `AUTO_CHAIN=1` to let the bridge promote a valid `next_suggestion` into a new Task Card automatically (capped by `AUTO_CHAIN_MAX` per hour and `AUTO_CHAIN_COOLDOWN_SEC`). If the suggestion is missing or too vague, and `PLANNER_FALLBACK=1`, a lightweight planner (`QUEUE_MODEL`) synthesizes a proper card. Defaults live in `foreman/config.yaml`.

### Docker

Build and run in watch mode:

```bash
docker build -t continuum-foreman .
docker run --rm -e OPENAI_API_KEY -e GT_TOKEN continuum-foreman
```

### systemd

Copy `continuum-foreman.service` to `/etc/systemd/system/` and adjust the environment variables:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now continuum-foreman
```

## Continuum Anchors

Reference documents:

- [JarvisPrime_BootProtocol](core/jarvisprime/JarvisPrime_BootProtocol.md)
- [continuum_master_final](core/jarvisprime/continuum_master_final.json)
- [continuum_ascension_path](core/jarvisprime/continuum_ascension_path.json)
- [continuum_true_endgame](core/jarvisprime/continuum_true_endgame.json)

## License
TBD

## Foreman ↔ Codex Bridge

`bridge/foreman_bridge.py` exposes a small FastAPI service that accepts Task Cards and forwards them to the executor.

- **Identity**: `foreman_id=jarvis-foreman`, `conversation_hint=continuum-foreman-thread`
- **Headers**: `X-Foreman-Id`, `X-Foreman-Conv`, `X-Foreman-Sign` (HMAC-SHA256 of body using `FOREMAN_SHARED_TOKEN`)
- Supports optional `X-Idempotency-Key` and enforces a rate limit of 6 task cards per minute
- `/v1/metrics` returns counters for accepted/patch/failed tasks and rate limiting events

Run the bridge:

```bash
uvicorn bridge.foreman_bridge:app --port 8787
```

Example call with signer:

```bash
export FOREMAN_SHARED_TOKEN=...
BODY='{"task_card":"Add LICENSE.md (MIT)."}'
SIG=$(python scripts/sign_taskcard.py "$BODY")
curl -sS -X POST http://localhost:8787/v1/taskcards \
  -H "Content-Type: application/json" \
  -H "X-Foreman-Id: jarvis-foreman" \
  -H "X-Foreman-Conv: continuum-foreman-thread" \
  -H "X-Foreman-Sign: $SIG" \
  -H "X-Idempotency-Key: demo-001" \
  -d "$BODY"

curl -sS http://localhost:8787/v1/baton
curl -sS http://localhost:8787/v1/health
curl -sS http://localhost:8787/v1/metrics
```

`/v1/health` does not require headers and returns `{ok:true}` when healthy.

### Parallel execution
The bridge queues Task Cards and executes them concurrently.
Configuration is in `foreman/config.yaml` (`pool.max_workers`, `pool.max_per_repo`, `pool.queue_max`).

Check queue state:

```bash
curl -sS http://localhost:8787/v1/queue | jq .
```

Cancel a queued task:

```bash
curl -X POST http://localhost:8787/v1/taskcards/cancel \
  -H "X-Foreman-Id: jarvis-foreman" \
  -H "X-Foreman-Conv: continuum-foreman-thread" \
  -H "X-Foreman-Sign: $(python scripts/sign_taskcard.py '{"task_id":"ID"}')" \
  -d '{"task_id":"ID"}'
```

### Go Live Smoke

Run a quick end-to-end check once the bridge is up:

```bash
export FOREMAN_SHARED_TOKEN=...
./scripts/smoke_live.sh
```

The script hits `/v1/health`, submits a sample Task Card with an idempotency key,
then prints the baton and metrics.

## Executor

`duet/duet_foreman.py` consumes Task Cards, calls the `CODEX_MODEL` via the OpenAI API, applies file operations, runs commands, and commits or patches.

- `QUEUE_MODEL` and `CODEX_MODEL` are read from `foreman/config.yaml` or env.
- Updates `foreman/baton.json` with the latest excerpt and suggestion.

## Fallback UI Bot

Disabled by default and unsafe without explicit selectors and user consent. Enable with `FALLBACK_UI_BOT=1` only when you know the DOM.

```bash
node fallback/ui_bot_playwright.mjs < task_card.txt
```

## CI / Tests

```bash
python -m py_compile bridge/foreman_bridge.py duet/duet_foreman.py
pytest -q
```

## Alchohalt MVP

Run the API:

```bash
uvicorn apps.alchohalt.app:app --port 8811
```
Visit `http://localhost:8811/alchohalt/ui` for a minimal web UI to select a user and record check-ins.

### Magic-Link Auth

Request a login link:

```bash
curl -sS -X POST http://localhost:8811/alchohalt/request_link \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","tz":"UTC"}'
```

The link is printed to the server logs. Visiting `/alchohalt/magic?token=...` sets an `alc_session` cookie. Logout via `POST /alchohalt/logout`.

### Caregiver Share

Each user has a public ID available via `GET /alchohalt/export/{user_id}`. Share a read-only dashboard:

```
http://localhost:8811/alchohalt/care/<public_id>
```

This view omits notes and email addresses.

### SMS Reminders

Set `ALC_TWILIO_SID`, `ALC_TWILIO_TOKEN`, and `ALC_TWILIO_FROM` to enable SMS reminders when a user has a `phone`. Otherwise SMS attempts are logged.

### CSV import/export

```bash
curl -sS http://localhost:8811/alchohalt/export_csv/1
curl -sS -X POST http://localhost:8811/alchohalt/import_csv \
  -F "email=me@example.com" -F "tz=UTC" -F "file=@data.csv"
```

### Metrics & Logs

```bash
curl -sS http://localhost:8811/alchohalt/metrics
jq . logs/alchohalt.jsonl | tail -n 5
```

Daily reminders via cron:

```bash
0 * * * * cd /repo && . .venv/bin/activate && python scripts/alchohalt_notify.py
```

Set SMTP env vars (`ALC_SMTP_HOST` etc.) to send real emails; otherwise reminders are logged.

### Docker Compose

Run both the API and notifier with persistent storage:

```bash
docker compose --env-file .env.example up -d
```

Add `--profile mailhog` when `MAILHOG_ENABLED=1` to start the dev SMTP server.

### Deploy (Render / Heroku)

Render uses `render.yaml` to define both the web service and a cron job that runs `scripts/alchohalt_notify.py` every 15 minutes. Health is checked via `GET /alchohalt/health` on port 8811 and returns commit hash, DB reachability, and config flags:

```bash
curl -sS http://localhost:8811/alchohalt/health
```

For Heroku/Railway-style platforms, use the provided `Procfile`:

```bash
web: uvicorn apps.alchohalt.app:app --host 0.0.0.0 --port ${PORT:-8811}
```

### Backups & Restore

Create a backup archive containing the SQLite DB, logs, and `.env.example`:

```bash
bash scripts/backup.sh
```

Restore from an archive (use `--force` to overwrite existing files):

```bash
bash scripts/restore.sh backups/alchohalt_YYYYmmdd_HHMM.tar.gz --force
```

### Rate Limits

Each user may make at most **five** check-in writes per UTC day. Additional attempts return `429 Too Many Requests` with a `Retry-After` header indicating seconds until the next day.

### Audit export

Audit events are recorded to `logs/audit.jsonl`. Export a redacted slice and optionally rotate processed lines:

```bash
python scripts/audit_export.py --from 2025-08-01 --to 2025-08-31 --format csv --rotate
```

### PWA (offline UI cache)

The web UI can be installed as a lightweight Progressive Web App. When visiting `/alchohalt/ui` in a browser, use “Install App” or “Add to Home Screen.” The service worker caches `GET /alchohalt/ui*` responses for offline viewing; check-ins while offline will fail until reconnected.

### Encryption-at-Rest

Generate a Fernet key and set `ALC_CRYPTO_KEY` to encrypt notes:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Use `scripts/migrate_encrypt_notes.py --dry-run` to preview, then run without `--dry-run` to encrypt existing notes.

### Data Retention

Set `ALC_RETENTION_DAYS` to redact notes older than N days (status and dates remain):

```bash
export ALC_RETENTION_DAYS=30
```

The retention pass runs as part of `alchohalt_notify` and logs counts only.

### Caregiver Digest

Users may provide `caregiver_email` to receive a daily summary at local midnight with today's result, current streak, and a link to the public caregiver page. The digest omits notes and other PII.

### Caregiver roles and alerts

Users may optionally consent to link caregivers with explicit roles:

```
POST /alchohalt/consent {"user_id":1,"consent":true}
POST /alchohalt/caregivers {"user_id":1,"caregiver_email":"c@e.com","role":"supporter"}
```

Roles:

- `viewer` – read-only access via `/alchohalt/care/{public_id}`
- `supporter` – receives alerts when rules fire

Alert rules are managed via `/alchohalt/alert_prefs` with per-channel options (`email` or `sms`) and thresholds:

- `slip` – notify on today's slip
- `two_in_7` – ≥2 slips in the last 7 days
- `three_in_30` – ≥3 slips in the last 30 days

Quiet hours (`quiet_hours_start`/`quiet_hours_end`) suppress alerts during specified local hours. Caregiver emails are masked in responses.

### RBAC and caregiver invites

UI write actions require a valid session cookie, and only the owner of a `user_id` may modify that user's records. Owners can invite caregivers via a signed link:

```bash
curl -X POST /alchohalt/invite_caregiver \
  -b alc_session=<cookie> \
  -d "user_id=1&caregiver_email=c@e.com&role=viewer"
```

The invite URL `/alchohalt/accept_caregiver?token=...` creates the link only if the user has granted caregiver consent.

### Applying patches

If the branch cannot be pushed directly, apply the patches:

```bash
git apply artifacts/patches/0001-feat-alchohalt-add-magic-link-authentication.patch
git apply artifacts/patches/0002-feat-alchohalt-add-caregiver-share-and-sms-reminders.patch
git apply artifacts/patches/0003-docs-alchohalt-note-patch-apply-steps.patch
git apply artifacts/patches/0004-docs-alchohalt-add-patch-apply-instructions.patch
```

## Multi-repo execution

The bridge accepts optional `repo` and `branch` fields when posting a Task Card. The executor clones the repository into
`workspaces/<owner>__<repo>` using a token from `foreman/config.yaml` (`token_env`). Example:

```bash
BODY='{"task_card":"Fix typo","repo":"YOURORG/your-repo","branch":"main"}'
SIG=$(python scripts/sign_taskcard.py "$BODY")
curl -X POST http://localhost:8787/v1/taskcards \
  -H "Content-Type: application/json" \
  -H "X-Foreman-Id: jarvis-foreman" \
  -H "X-Foreman-Conv: continuum-foreman-thread" \
  -H "X-Foreman-Sign: $SIG" \
  -d "$BODY"
```

### Persistent queue & DLQ
The worker pool persists enqueued items to `foreman/queue.jsonl` and failed ones to `foreman/dlq.jsonl`. Inspect the dead-letter queue:

```bash
curl -sS http://localhost:8787/v1/dlq | jq .
# requeue a task
curl -sS -X POST http://localhost:8787/v1/dlq/requeue \
  -H "X-Foreman-Id: jarvis-foreman" \
  -H "X-Foreman-Conv: continuum-foreman-thread" \
  -H "X-Foreman-Sign: $SIG" \
  -d '{"task_id":"abc123"}'
```

### Repo safety policy
Author `foreman/policy.yaml` to restrict file edits per repo:

```yaml
repos:
  YOURORG/alchohalt:
    max_files: 20
    allow_paths: ["apps/alchohalt/**", "tests/**", "README.md"]
    deny_paths: ["scripts/backup.sh", ".github/workflows/**"]
defaults:
  max_files: 15
```

### PR checks & automerge
In PR mode the executor sets commit status context `codex/tests`, applies label `autofeature`, and when `AUTOMERGE=1` and tests pass it enables GitHub auto-merge.

You can also route via a policy key defined in `foreman/config.yaml`:

```bash
BODY='{"task_card":"Ship docs homepage","policy_key":"docs"}'
SIG=$(python scripts/sign_taskcard.py "$BODY")
curl -X POST http://localhost:8787/v1/taskcards \
  -H "Content-Type: application/json" \
  -H "X-Foreman-Id: jarvis-foreman" \
  -H "X-Foreman-Conv: continuum-foreman-thread" \
  -H "X-Foreman-Sign: $SIG" \
  -d "$BODY"
```

To stop workers gracefully (useful in tests), call the shutdown endpoint:

```bash
SIG=$(python scripts/sign_taskcard.py "")
curl -X POST http://localhost:8787/v1/admin/shutdown \
  -H "X-Foreman-Id: jarvis-foreman" \
  -H "X-Foreman-Conv: continuum-foreman-thread" \
  -H "X-Foreman-Sign: $SIG"
```

## Priority & Dedupe

Task cards can be enqueued with a priority hint (`high`, `normal`, `low`).
Duplicate payloads are deduplicated by content hash and return the original `task_id`.

```bash
BODY='{"task_card":"Hotfix", "priority":"high"}'
SIG=$(python scripts/sign_taskcard.py "$BODY")
curl -X POST http://localhost:8787/v1/taskcards \
  -H "Content-Type: application/json" \
  -H "X-Foreman-Id: jarvis-foreman" \
  -H "X-Foreman-Conv: continuum-foreman-thread" \
  -H "X-Foreman-Sign: $SIG" \
  -d "$BODY"
```

## Repo Inference

If no `repo` or `policy_key` is provided, the bridge infers a target repo by
matching keywords defined in `foreman/config.yaml` and reports the reason in
the response.

## PR Mode

When `PR_MODE=1` or a repo config has `pr_mode: true`, tasks run on a temporary
`autofeature/<task_id>` branch and a pull request is opened automatically using
either a GitHub App token or a PAT.

## Clean Teardown

`/v1/admin/shutdown` drains the queue, cancels pending tasks, and stops workers
within a configurable timeout (`SHUTDOWN_TIMEOUT_SEC`).

## Offline mode (write-through)

When the PWA is offline, check-ins are stored in an IndexedDB queue. Once connectivity returns, the service worker flushes the
queue to `/alchohalt/checkins/bulk` in batches. The base template displays a banner when offline.
