import importlib
import json
import os
import sys
import shutil
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))


def reload_stub():
    if "src.serve.server_stub" in sys.modules:
        del sys.modules["src.serve.server_stub"]
    return importlib.import_module("src.serve.server_stub")


def test_runtime_fallback(tmp_path, monkeypatch, capsys):
    # ensure no quant artifacts
    qdir = Path("artifacts/quant")
    if qdir.exists():
        shutil.rmtree(qdir)
    monkeypatch.setenv("INFER_RUNTIME", "int8")
    stub = reload_stub()
    out = capsys.readouterr().out
    assert stub.RUNTIME == "fp16"
    assert "falling back" in out

    # create manifest
    qdir.mkdir(parents=True)
    (qdir / "model_index.json").write_text(json.dumps({"runtime_hint": "int8"}))
    stub = reload_stub()
    assert stub.RUNTIME == "int8"
