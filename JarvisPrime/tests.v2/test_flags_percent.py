from src.serve import flags


def test_canary_percent_split():
    flags._FLAGS["lineup_agent"]["state"] = "canary"
    flags._FLAGS["lineup_agent"]["percent"] = 25
    flags._save()
    assert flags.reason("lineup_agent", "user1", None) == "not_canary"
    assert flags.allowed("lineup_agent", "user2", None)


def test_canary_slo_throttle(tmp_path):
    flags._FLAGS["lineup_agent"]["percent"] = 25
    flags._save()
    before = flags.dump()["lineup_agent"]["percent"]
    flags.slo_breach("lineup_agent")
    after = flags.dump()["lineup_agent"]["percent"]
    assert after <= before // 2
    flags._FLAGS["lineup_agent"]["percent"] = before
    flags._save()
