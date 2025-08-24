import argparse
import json
import time
from pathlib import Path
import urllib.request


def run(runtime: str, iters: int, warmup: int, urlopen=urllib.request.urlopen) -> Path:
    url = "http://127.0.0.1:8000/chat"
    payload = json.dumps({"message": "voice_mirror", "args": {"text": "hi"}}).encode()
    headers = {"Content-Type": "application/json"}
    lat: list[float] = []
    for i in range(iters):
        req = urllib.request.Request(url, data=payload, headers=headers)
        start = time.time()
        with urlopen(req) as r:  # type: ignore
            r.read()
        dur = (time.time() - start) * 1000
        if i >= warmup:
            lat.append(dur)
    lat.sort()
    def pct(p):
        if not lat:
            return 0.0
        k = int((len(lat) - 1) * p)
        return lat[k]
    p50 = pct(0.5)
    p95 = pct(0.95)
    tps = len(lat) / (sum(lat) / 1000) if lat else 0.0
    out = {
        "runtime": runtime,
        "iters": iters,
        "warmup": warmup,
        "p50_ms": round(p50, 3),
        "p95_ms": round(p95, 3),
        "tps": round(tps, 3),
    }
    out_dir = Path("logs/perf")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{time.strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(out))
    print(json.dumps(out))
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime", default="fp16")
    ap.add_argument("--iters", type=int, default=25)
    ap.add_argument("--warmup", type=int, default=5)
    args = ap.parse_args()
    run(args.runtime, args.iters, args.warmup)


if __name__ == "__main__":
    main()
