from pathlib import Path
import sys
import pathlib
import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.data.adapters import base, ownership_dkcsv, results_dkcsv  # register modules


def test_registry_contains_adapters():
    assert 'ownership:dkcsv' in base.ADAPTERS
    assert 'results:dkcsv' in base.ADAPTERS


def test_ownership_adapter_schema(tmp_path):
    bad = tmp_path / 'bad.csv'
    bad.write_text('player_id,team,proj_points\n1,A,10')
    with pytest.raises(ValueError):
        base.get('ownership:dkcsv').load(bad)


def test_results_adapter_schema(tmp_path):
    bad = tmp_path / 'bad.csv'
    bad.write_text('contest_id,slate_id\n1,slate')
    with pytest.raises(ValueError):
        base.get('results:dkcsv').load(bad)
