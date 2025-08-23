VENV=.venv
PY=./$(VENV)/bin/python
PIP=./$(VENV)/bin/pip
PYTHONPATH=src

.PHONY: venv stub serve_local test lint

venv:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip >/dev/null
	@$(PIP) install -q pytest pyyaml || true
	@$(PIP) install -q typing-extensions || true
	@$(PIP) install -q uvloop || true

stub: venv
	@PYTHONPATH=$(PYTHONPATH) $(PY) -m src.serve.server_stub

serve_local: venv
	@bash scripts/bootstrap_local.sh || true
	@$(MAKE) stub

test: venv
	@PYTHONPATH=$(PYTHONPATH) $(PY) scripts/run_tests.py || true
	@echo "Wrote test summary (if available) to logs/test_summary.json"

lint: venv
	@$(PY) -m compileall src || true
	@command -v ruff >/dev/null 2>&1 && ruff check src || true
