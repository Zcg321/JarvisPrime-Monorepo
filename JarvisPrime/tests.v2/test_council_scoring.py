from src.tools.dfs import predict_lineup


def test_scoring_modes_change_selection():
    players = [
        {"name": "A", "pos": "PG", "cost": 10, "proj": 10, "player_id": "A"},
        {"name": "B", "pos": "PG", "cost": 10, "proj": 9, "player_id": "B"},
    ]
    ownership = {"A": 50.0, "B": 1.0}
    lineup_gohan = predict_lineup(players, 100, {"UTIL": 1}, scoring_mode="gohan", ownership=ownership)
    lineup_goku = predict_lineup(players, 100, {"UTIL": 1}, scoring_mode="goku", ownership=ownership)
    assert lineup_gohan["lineup"][0]["name"] == "A"
    assert lineup_goku["lineup"][0]["name"] == "B"
