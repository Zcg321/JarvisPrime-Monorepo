import json
import urllib.request
import subprocess
from pathlib import Path


def test_dashboard_api(server):
    subprocess.run(["python", "scripts/dashboard.py"], check=True)
    req = urllib.request.Request(
        f"http://127.0.0.1:{server}/dashboard/json",
        headers={"Authorization": "Bearer ADMIN_TOKEN"},
    )
    data = json.loads(urllib.request.urlopen(req).read())
    assert "health" in data
    html = Path("artifacts/reports/dashboard.html").read_text()
    assert "setInterval" in html
