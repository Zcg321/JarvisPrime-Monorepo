import json
from pathlib import Path
from src.data import results

def test_results_ingest(tmp_path):
    csv_path = tmp_path / "res.csv"
    csv_path.write_text(
        "contest_id,slate_id,lineup_id,player_id,fpts,rank,payout\n" +
        "1,S1,1,P1,10,1,20\n" +
        "2,S1,2,P2,15,2,5\n"
    )
    out = results.ingest(str(csv_path))
    report = json.loads(Path(out["report_path"]).read_text())
    assert report["slate_id"] == "S1"
    assert "P1" in report["players"]
    roi_file = Path("logs/ghosts/roi.jsonl")
    assert roi_file.exists()
    lines = roi_file.read_text().strip().splitlines()
    assert any("P1" in line for line in lines)
