Jarvis Prime Foreman (Nova-Prime v2) — Step A
- Land Savepoint Logger, Voice Mirror, JSON Guard as additive FastAPI plugin with tests.
- Branch: feat/plugins-savepoint-voice-jsonguard

After applying:
- pip install -r requirements.txt
- pytest -q
- uvicorn jarvis_plugins.app:app --port 8099 --reload
