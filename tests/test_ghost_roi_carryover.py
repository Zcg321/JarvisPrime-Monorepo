import os
import os
import tempfile
from datetime import datetime, timezone
import importlib
import sys
import pathlib

if str(pathlib.Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from src.tools import dfs


def setup_module(module):
    module.tmp = tempfile.NamedTemporaryFile(delete=False)
    os.environ['GHOST_ROI_PATH'] = module.tmp.name
    import src.tools.ghost_roi as gr
    importlib.reload(gr)
    module.gr = gr


def teardown_module(module):
    try:
        os.unlink(module.tmp.name)
    except OSError:
        pass


def test_ema_and_bias():
    day1 = datetime(2025,1,1,tzinfo=timezone.utc).timestamp()
    day2 = datetime(2025,1,2,tzinfo=timezone.utc).timestamp()
    gr.record_daily_roi([
        {'player_id':'A','slate_type':'classic','roi':0.2},
        {'player_id':'B','slate_type':'classic','roi':-0.1}
    ], ts=day1)
    gr.record_daily_roi([
        {'player_id':'A','slate_type':'classic','roi':0.2}
    ], ts=day2)
    ema = gr.load_ema('A','classic',lookback_days=400,alpha=0.5)
    assert round(ema,3) == 0.2
    players = [
        {'name':'A','pos':'PG','cost':100,'proj':9.0},
        {'name':'B','pos':'PG','cost':100,'proj':10.0}
    ]
    lineup = dfs.predict_lineup(players,100,{"PG":1},{'lookback_days':400,'alpha':0.35})
    assert lineup['lineup'][0]['name'] == 'A'
