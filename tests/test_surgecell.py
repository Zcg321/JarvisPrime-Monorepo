import json

from src.core import anchors
from src.tools import surgecell


def test_default_allocation_sums_to_one():
    alloc = surgecell.allocate()
    assert abs(sum(alloc.values()) - 1.0) < 1e-6


def test_default_matches_boot_protocol():
    boot = anchors.load_all()['boot']
    expected = anchors.surge_allocations(boot)
    assert surgecell.DEFAULT == expected


def test_usage_downweights_heavy_tool():
    alloc = surgecell.allocate(history={"DFS": 100})
    assert alloc["DFS"] < 0.1
    assert abs(sum(alloc.values()) - 1.0) < 0.05


def test_allocation_persisted(tmp_path, monkeypatch):
    path = tmp_path / "logs/savepoints"
    monkeypatch.chdir(tmp_path)
    alloc = surgecell.allocate()
    file_path = path / "surgecell_last.json"
    assert file_path.exists()
    data = json.loads(file_path.read_text())
    assert alloc == data


def test_load_last_uses_persisted(monkeypatch, tmp_path):
    path = tmp_path / "logs/savepoints"
    monkeypatch.chdir(tmp_path)
    first = surgecell.allocate(weights={"DFS": 0.4})
    second = surgecell.allocate()
    assert second == first
