import argparse
from src.savepoint.logger import rotate_logs


def main():
    p = argparse.ArgumentParser(description="rotate savepoints")
    p.add_argument("--keep", type=int, default=500)
    p.add_argument("--days", type=int, default=14)
    args = p.parse_args()
    removed = rotate_logs(args.keep, args.days)
    print(f"removed {removed}")


if __name__ == "__main__":
    main()
