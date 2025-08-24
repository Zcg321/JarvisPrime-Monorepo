from jarvisprime.client import JarvisPrime


def main(max_seconds: int = 2) -> None:
    cli = JarvisPrime()
    for evt in cli.stream_alerts(max_seconds=max_seconds):
        print(evt)
        break


if __name__ == "__main__":  # pragma: no cover
    main()
