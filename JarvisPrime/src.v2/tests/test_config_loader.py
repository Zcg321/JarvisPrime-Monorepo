import os
import importlib
import json
import pytest
from src.config.loader import load_config


def test_env_overlay(monkeypatch):
    monkeypatch.setenv('FOO__BAR', '1')
    cfg = load_config()
    assert cfg['foo']['bar'] == 1


def test_bad_schema(monkeypatch):
    monkeypatch.setenv('FOO__BAR', 'not_int')
    with pytest.raises(Exception):
        load_config()
