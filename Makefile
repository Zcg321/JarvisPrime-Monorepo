.PHONY: test lint

test:
pytest

lint:
flake8 JarvisPrime
