import os
import importlib
from datetime import date
import tempfile


def setup_module(module):
    module.tmp = tempfile.NamedTemporaryFile(delete=False)
    os.environ["ALCHOHALT_DB"] = module.tmp.name
    global alchohalt
    alchohalt = importlib.import_module("src.tools.alchohalt")


def teardown_module(module):
    module.tmp.close()
    try:
        os.unlink(module.tmp.name)
    except OSError:
        pass


def test_metrics_and_streak():
    alchohalt._write_entry("2023-10-30", "halted")
    alchohalt._write_entry("2023-10-31", "halted")
    alchohalt._write_entry("2023-11-01", "slipped")
    alchohalt._write_entry("2023-11-02", "halted")
    alchohalt._write_entry("2023-11-03", "halted")
    metrics = alchohalt.metrics(today=date(2023, 11, 3))
    assert metrics["streak"] == 2
    assert metrics["halted7"] == 4
    assert metrics["halted30"] == 4
    assert metrics["series7"] == [0, 0, 1, 1, 0, 1, 1]
    assert metrics["lastSlipDate"] == "2023-11-01"


def test_schedule_stores_time():
    res = alchohalt.schedule(20, 15)
    assert res == {"reminder_hour": 20, "reminder_minute": 15}
