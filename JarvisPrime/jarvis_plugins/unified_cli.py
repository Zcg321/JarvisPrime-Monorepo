from __future__ import annotations
import argparse, json, sys

from .savepoint import SavepointLogger
from .voice_mirror import VoiceMirror
from JarvisOrigin.src.export import int8_export


def main(argv=None):
    parser = argparse.ArgumentParser("jarvisctl")
    sub = parser.add_subparsers(dest="cmd")

    spc = sub.add_parser("save"); spc.add_argument("--tag", default="manual"); spc.add_argument("--payload", default="{}")
    spr = sub.add_parser("recent"); spr.add_argument("-n", type=int, default=10)
    vmr = sub.add_parser("reflect"); vmr.add_argument("text", nargs="+")
    exp = sub.add_parser("export-int8"); exp.add_argument("--out", default="artifacts/export/int8")

    args = parser.parse_args(argv)

    if args.cmd == "save":
        out = SavepointLogger().create(json.loads(args.payload), tag=args.tag)
        print(json.dumps(out)); return 0
    if args.cmd == "recent":
        print(json.dumps({"items": SavepointLogger().recent(args.n)})); return 0
    if args.cmd == "reflect":
        out = VoiceMirror().reflect(" ".join(args.text))
        print(json.dumps(out, ensure_ascii=False)); return 0
    if args.cmd == "export-int8":
        try:
            import torch
            net = torch.nn.Sequential(torch.nn.Linear(16,16), torch.nn.ReLU(), torch.nn.Linear(16,16))
            out = int8_export.dynamic_int8_export(net, args.out, {"note":"cli export"})
            print("INT8 export written to:", out)
        except ModuleNotFoundError:
            out = int8_export.dynamic_int8_export(None, args.out, {"note":"cli export"})
            print("Torch missing; meta only at:", out)
        return 0
    parser.print_help(); return 1


if __name__ == "__main__":
    raise SystemExit(main())
