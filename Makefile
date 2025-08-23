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

# ---- Jarvis Plugins (Savepoint, VoiceMirror, JSONGuard)
.PHONY: deps-plugins plugins-serve test-plugins serve-main test-all cli-save cli-recent cli-reflect

deps-plugins:
	pip install -r requirements.txt

plugins-serve:
	uvicorn jarvis_plugins.app:app --reload --port 8099

test-plugins:
	pytest -q tests/test_json_guard.py tests/test_plugins_api.py

serve-main:
	uvicorn JarvisOrigin.src.serve.server:app --reload --port 8080

test-all:
	PYTHONPATH=$(PWD) pytest -q tests/test_json_guard.py tests/test_plugins_api.py tests/test_server_mount.py

cli-save:
	PYTHONPATH=$(PWD) python -m jarvis_plugins.cli save --tag demo --payload '{"x":1}'

cli-recent:
	PYTHONPATH=$(PWD) python -m jarvis_plugins.cli recent -n 5

cli-reflect:
	PYTHONPATH=$(PWD) python -m jarvis_plugins.cli reflect "protect the flame"

.PHONY: test-contracts test-crash export-int8
test-contracts:
	PYTHONPATH=$(PWD) pytest -q tests/test_json_contracts.py
test-crash:
	PYTHONPATH=$(PWD) pytest -q tests/test_autoresurrect.py
export-int8:
	PYTHONPATH=$(PWD) python scripts/export_int8.py

.PHONY: cli-unified cli-export-int8
cli-unified:
	PYTHONPATH=$(PWD) python -m jarvis_plugins.unified_cli --help
cli-export-int8:
	PYTHONPATH=$(PWD) python -m jarvis_plugins.unified_cli export-int8 --out artifacts/export/int8

.PHONY: rag-rebuild ci
rag-rebuild:
	PYTHONPATH=$(PWD) python scripts/rag_rebuild.py

ci:
	PYTHONPATH=$(PWD) pytest -q   tests/test_json_guard.py   tests/test_plugins_api.py   tests/test_server_mount.py   tests/test_json_contracts.py   tests/test_autoresurrect.py   tests/test_export_guard.py   tests/test_unified_cli.py   tests/test_contract_schemas.py   tests/test_dna_sync.py

.PHONY: ci-report
ci-report:
	PYTHONPATH=$(PWD) pytest -q --junitxml=artifacts/ci/junit.xml
	@echo "JUnit report at artifacts/ci/junit.xml"
