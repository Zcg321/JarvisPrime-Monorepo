# Step B — Integration

- Plugins mounted at `/plugins`
- Reflex ancestry logger
- JSONGuard helper
- CLI: `python -m jarvis_plugins.cli`

## Run
make deps-plugins
PYTHONPATH=$PWD pytest -q tests/test_json_guard.py tests/test_plugins_api.py tests/test_server_mount.py
make plugins-serve
make serve-main
