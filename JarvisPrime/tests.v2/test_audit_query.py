import json
import subprocess
from pathlib import Path


def test_audit_query(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts/audit_query.py"
    monkeypatch.chdir(tmp_path)
    log_dir = Path("logs/audit")
    log_dir.mkdir(parents=True, exist_ok=True)
    sample = {
        "ts_iso": "2025-10-25T12:00:00+00:00",
        "tool": "dfs",
        "args_redacted": {},
        "token_id": "user1",
        "result_status": 200,
    }
    (log_dir / "audit_test.jsonl").write_text(json.dumps(sample) + "\n")
    res = subprocess.run(
        [
            "python",
            str(script),
            "--tool",
            "dfs",
            "--token-id",
            "user1",
            "--since",
            "2025-10-25T00:00Z",
            "--until",
            "2025-10-25T23:59Z",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(res.stdout)
    assert out == [sample]
    res_csv = subprocess.run(
        [
            "python",
            str(script),
            "--tool",
            "dfs",
            "--format",
            "csv",
            "--since",
            "2025-10-25T00:00Z",
            "--until",
            "2025-10-25T23:59Z",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = res_csv.stdout.strip().splitlines()
    assert lines[0].split(",") == ["ts", "tool", "token_id", "result_status"]
    assert lines[1].endswith(",dfs,user1,200")
    res_sum = subprocess.run(
        [
            "python",
            str(script),
            "--summary",
            "--since",
            "2025-10-25T00:00Z",
            "--until",
            "2025-10-25T23:59Z",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    summ = json.loads(res_sum.stdout)
    assert summ["per_tool"].get("dfs") == 1
