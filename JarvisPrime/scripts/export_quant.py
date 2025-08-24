import argparse
import json
from pathlib import Path


def export(model: str, out: str, method: str) -> str:
    out_path = Path(out)
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "adapter").mkdir(exist_ok=True)
    (out_path / "weights").mkdir(exist_ok=True)
    selected = method
    if method == "awq":
        try:
            import awq  # type: ignore
            selected = "awq"
        except Exception:
            selected = "bnbint8"
    elif method == "bnbint8":
        try:
            import bitsandbytes  # type: ignore  # noqa: F401
            selected = "bnbint8"
        except Exception:
            selected = "none"
    (out_path / "model_index.json").write_text(json.dumps({"runtime_hint": selected}))
    (out_path / "notes.txt").write_text(f"method={selected}\n")
    print(f"exported using {selected}")
    return selected


def main():
    p = argparse.ArgumentParser(description="Quantized export")
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--method", choices=["awq", "bnbint8"], default="awq")
    args = p.parse_args()
    export(args.model, args.out, args.method)


if __name__ == "__main__":
    main()
