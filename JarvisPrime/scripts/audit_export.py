import argparse
from pathlib import Path
from src.serve.audit_export import export_audit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--token-id', required=True)
    ap.add_argument('--since', required=True)
    ap.add_argument('--until', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    path, manifest = export_audit(args.token_id, args.since, args.until, Path(args.out))
    print(str(path))


if __name__ == '__main__':
    main()
