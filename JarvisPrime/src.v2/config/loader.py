import os
import yaml
from pathlib import Path
from typing import Any, Dict
try:
    import jsonschema
except Exception:  # pragma: no cover
    jsonschema = None

CONFIG_DIR = Path("configs")
SCHEMA_FILE = CONFIG_DIR / "schema.yaml"


def _overlay_env(cfg: Dict[str, Any]) -> Dict[str, Any]:
    for key, val in os.environ.items():
        if "__" not in key:
            continue
        parts = key.lower().split("__")
        ref = cfg
        for p in parts[:-1]:
            ref = ref.setdefault(p, {})
        try:
            cast = int(val)
        except ValueError:
            try:
                cast = float(val)
            except ValueError:
                if val.lower() in {"true", "false"}:
                    cast = val.lower() == "true"
                else:
                    cast = val
        ref[parts[-1]] = cast
    return cfg


def load_config() -> Dict[str, Any]:
    cfg: Dict[str, Any] = {}
    for yml in CONFIG_DIR.glob("*.yaml"):
        if yml.name == "schema.yaml":
            continue
        cfg[yml.stem] = yaml.safe_load(yml.read_text())
    cfg = _overlay_env(cfg)
    if SCHEMA_FILE.exists():
        schema = yaml.safe_load(SCHEMA_FILE.read_text())
        if jsonschema is not None:
            jsonschema.validate(cfg, schema)
        else:  # minimal manual check
            def _check(node, sch):
                t = sch.get("type")
                if t == "object":
                    assert isinstance(node, dict), "object expected"
                    props = sch.get("properties", {})
                    for k, v in props.items():
                        if k in node:
                            _check(node[k], v)
                elif t == "number":
                    assert isinstance(node, (int, float)), "number expected"
                elif t == "integer":
                    assert isinstance(node, int), "integer expected"
            _check(cfg, schema)
    return cfg
