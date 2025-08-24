import json
from pathlib import Path

def _agg(files):
    if not files:
        return {}
    keys = ["p50_ms", "p95_ms", "tps"]
    agg = {k: 0.0 for k in keys}
    for f in files:
        data = json.loads(Path(f).read_text())
        for k in keys:
            agg[k] += float(data.get(k, 0.0))
    for k in keys:
        agg[k] /= len(files)
    return agg

def main() -> None:
    perf_dir = Path("logs/perf")
    fp16_files = sorted(str(p) for p in perf_dir.glob("*fp16*.json"))
    int8_files = sorted(str(p) for p in perf_dir.glob("*int8*.json"))
    fp16 = _agg(fp16_files)
    int8 = _agg(int8_files)
    delta = {k: int8.get(k, 0.0) - fp16.get(k, 0.0) for k in fp16}
    out = {
        "fp16": fp16,
        "int8": int8,
        "delta": delta,
        "quant_available": Path("artifacts/quant/model_index.json").exists(),
    }
    perf_dir.mkdir(parents=True, exist_ok=True)
    (perf_dir / "compare.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out))

if __name__ == "__main__":
    main()
