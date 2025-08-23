from __future__ import annotations
import os, json
from pathlib import Path

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def dynamic_int8_export(model=None, out_dir: str = "artifacts/export/int8", meta: dict | None = None) -> str:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    meta_file = out / "export_meta.json"
    if not HAS_TORCH:
        meta_file.write_text(json.dumps({"error": "torch not installed"}, indent=2), encoding="utf-8")
        return str(out)
    if model is None:
        raise ValueError("Provide a torch.nn.Module for export")
    model.eval()
    q_model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
    sd_path = out / "model_int8_state.pt"
    ts_path = out / "model_int8_script.pt"
    torch.save(q_model.state_dict(), sd_path)
    try:
        torch.jit.script(q_model).save(str(ts_path))
    except Exception:
        ts_path = None
    meta = {"format": "int8-dynamic", "torchscript": bool(ts_path), "extra": meta or {}}
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return str(out)

if __name__ == "__main__":
    print(dynamic_int8_export())
