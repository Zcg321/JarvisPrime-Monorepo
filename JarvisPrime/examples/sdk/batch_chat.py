from jarvisprime.client import JarvisPrime


def main() -> None:
    cli = JarvisPrime()
    msgs = [
        {"message": "savepoint", "args": {"event": "test", "payload": {}}},
        {"message": "unknown", "args": {}},
    ]
    print(cli.chat_batch(msgs))


if __name__ == "__main__":  # pragma: no cover
    main()
