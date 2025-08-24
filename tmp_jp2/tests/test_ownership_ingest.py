import tempfile
from pathlib import Path
import pytest

from src.data.ownership import load_daily


def test_load_daily_success(tmp_path):
    csv = tmp_path / 'own.csv'
    csv.write_text('player_id,team,proj_points,field_own_pct\nP1,AAA,10,20\n')
    data = load_daily(csv)
    assert data[0]['player_id'] == 'P1'
    assert data[0]['proj_points'] == 10.0
    # second call hits cache
    data2 = load_daily(csv)
    assert data2 is data


def test_bad_schema(tmp_path):
    csv = tmp_path / 'bad.csv'
    csv.write_text('player,team,proj_points\nP1,AAA,10\n')
    with pytest.raises(ValueError):
        load_daily(csv)
