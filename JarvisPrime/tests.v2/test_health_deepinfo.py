import json
import urllib.request


def test_health_deepinfo(server):
    port = server
    data = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/health").read())
    for key in [
        "uptime_s",
        "config_sha",
        "tokens_configured",
        "alerts_total",
        "audit_files",
        "savepoints_count",
    ]:
        assert key in data
