from src.tools import validate_inputs


def test_missing_player(tmp_path):
    own = tmp_path / "own.csv"
    own.write_text("player_id,team,proj_points,field_own_pct\nA,AAA,10,0.1\n")
    lineups = [{"players": [{"player_id": "B", "salary": 1000}]}]
    report = validate_inputs.validate(str(own), None, lineups)
    assert report["missing_from_ownership"] == ["B"]
    assert report["salary_violations"] == 0
