import argparse, json
from .savepoint import SavepointLogger
from .voice_mirror import VoiceMirror

def main(argv=None):
    parser = argparse.ArgumentParser("jarvis-cli")
    sub = parser.add_subparsers(dest="cmd")

    s = sub.add_parser("save")
    s.add_argument("--tag", default="manual")
    s.add_argument("--payload", default="{}")

    r = sub.add_parser("recent")
    r.add_argument("-n", type=int, default=10)

    v = sub.add_parser("reflect")
    v.add_argument("text", nargs="+")

    args = parser.parse_args(argv)
    if args.cmd == "save":
        out = SavepointLogger().create(json.loads(args.payload), tag=args.tag)
        print(json.dumps(out))
        return 0
    if args.cmd == "recent":
        out = SavepointLogger().recent(args.n)
        print(json.dumps({"items": out}))
        return 0
    if args.cmd == "reflect":
        out = VoiceMirror().reflect(" ".join(args.text))
        print(json.dumps(out, ensure_ascii=False))
        return 0
    parser.print_help()
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
