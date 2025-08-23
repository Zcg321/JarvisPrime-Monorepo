# Step G — Observability Pack

## Metrics
- `/plugins/metrics` returns uptime and internal counters.
- Use `jarvis_plugins.metrics.inc("key")` to instrument.

## Logs
- Structured JSON logs at `artifacts/logs/jarvis.log`.
- Each savepoint automatically logs `{ "event": "savepoint", ... }`.

## CI
- `make ci-report` generates `artifacts/ci/junit.xml` for integration with CI systems.

## Tests
- `pytest tests/test_metrics_logs.py` verifies metrics and logging.
