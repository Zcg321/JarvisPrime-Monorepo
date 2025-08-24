from jarvis_plugins.json_guard import JSONGuard
import pytest


def test_fenced_json():
    text = """Here:
```json
{"a": 1, "b": "x"}
```"""
    data, mode = JSONGuard.extract_and_validate(text)
    assert data["a"] == 1
    assert mode == "fenced"


def test_raw_json():
    text = "prefix {\"k\": 3} suffix"
    data, mode = JSONGuard.extract_and_validate(text)
    assert data["k"] == 3
    assert mode == "raw"


def test_invalid():
    with pytest.raises(ValueError):
        JSONGuard.extract_and_validate("no json here")
