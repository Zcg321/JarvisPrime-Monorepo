import argparse
import json
import os

from jarvisprime.client import JarvisPrime


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("health")
    sub.add_parser("metrics")
    sub.add_parser("list-tools")
    chat = sub.add_parser("chat")
    chat.add_argument("--message", required=True)
    chat.add_argument("--args", default="{}")
    ae = sub.add_parser("audit-export")
    ae.add_argument("--token-id", required=True)
    ae.add_argument("--since", required=True)
    ae.add_argument("--until", required=True)
    args = parser.parse_args(argv)
    client = JarvisPrime()
    if args.cmd == "health":
        print(json.dumps(client.health()))
    elif args.cmd == "metrics":
        print(json.dumps(client.metrics()))
    elif args.cmd == "list-tools":
        print(json.dumps(client.list_tools()))
    elif args.cmd == "chat":
        print(json.dumps(client.chat(args.message, json.loads(args.args))))
    elif args.cmd == "audit-export":
        path = f"/audit/export?token_id={args.token_id}&since={args.since}&until={args.until}"
        print(json.dumps(client.admin_get(path)))


if __name__ == "__main__":  # pragma: no cover
    main()
