import json
import urllib.request
import urllib.error
import pytest


def _post(port, obj):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps(obj).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.getcode(), json.loads(resp.read().decode())


def test_list_tools(server):
    port = server
    code, res = _post(port, {"message": "list_tools"})
    assert code == 200
    for name in ["dfs", "savepoint", "ghost_dfs.seed", "dfs_portfolio", "results_ingest", "bankroll_alloc", "portfolio_eval"]:
        assert name in res["tools"]


def test_bad_payload(server):
    port = server
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=b"not json",
        headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=5)
    assert exc.value.code == 400
    body = exc.value.read().decode()
    data = json.loads(body)
    assert data.get('error') == 'BadRequest'
    assert 'reason' in data


def test_dispatch(server):
    port = server
    code, res = _post(port, {"message": "dfs", "args": {"players": [], "budget": 0}})
    assert code == 200 and "lineup" in res
    code, res = _post(port, {"message": "savepoint", "args": {"event": "t", "payload": {}}})
    assert code == 200 and "path" in res
    code, res = _post(port, {"message": "ghost_dfs.seed", "args": {"slate_id": "T", "seed": 1}})
    assert code == 200 and "pool" in res


def test_new_endpoints(server, tmp_path):
    csv = tmp_path / "r.csv"
    csv.write_text("contest_id,slate_id,lineup_id,player_id,fpts,rank,payout\n1,S,1,P,10,1,5\n")
    port = server
    code, _ = _post(port, {"message": "results_ingest", "args": {"path": str(csv)}})
    assert code == 200
    bad = {"message": "bankroll_alloc", "args": {}}
    port = server
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps(bad).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=5)
    assert exc.value.code == 400
    own = tmp_path / "own.csv"
    own.write_text("player_id,team,proj_points,field_own_pct\nP,T,10,0.1\n")
    code, res = _post(port, {"message": "portfolio_eval", "args": {"lineups": [], "ownership_csv": str(own)}})
    assert code == 200 and "ev" in res


def test_submit_plan_and_bad_reason(server):
    port = server
    code, res = _post(port, {
        "message": "submit_plan",
        "args": {"slate_id": "S", "lineups": [], "bankroll": 100, "entry_fee": 1.0, "max_entries": 5},
    })
    assert code == 200 and "proposed_entries" in res
    bad = {"message": "schedule_query", "args": {"start": "bad", "end": "2020-01-01"}}
    port = server
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps(bad).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=5)
    assert exc.value.code == 400


def test_dfs_portfolio_payloads(server):
    port = server
    bad = {"message": "dfs_portfolio", "args": {"slates": "oops"}}
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps(bad).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=5)
    assert exc.value.code == 400
    code, res = _post(port,
        {
            "message": "dfs_portfolio",
            "args": {
                "slates": [
                    {"id": "S1", "type": "classic"},
                    {"id": "S2", "type": "showdown"},
                ],
                "n_lineups": 2,
                "seed": 1,
            },
        }
    )
    assert code == 200 and "lineups" in res
