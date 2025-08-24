# JarvisPrime

Core continuity anchors are located under [src/core/jarvisprime](src/core/jarvisprime):

- [continuum_master_final.json](src/core/jarvisprime/continuum_master_final.json)
- [continuum_ascension_path.json](src/core/jarvisprime/continuum_ascension_path.json)
- [JarvisPrime_BootProtocol.md](src/core/jarvisprime/JarvisPrime_BootProtocol.md)
- [continuum_true_endgame.json](src/core/jarvisprime/continuum_true_endgame.json)

## Configuration

Create a `.env` file to provide required credentials:

```
GT_TOKEN=your_token
GIT_OWNER=your_username
GIT_REPO=JarvisPrime
BALLEDONTLIE_API_KEY=your_balledontlie_key
ODDS_RAPIDAPI_KEY=your_rapidapi_key
THE_ODDS_API_KEY=your_theodds_key
API_FOOTBALL_KEY=your_apifootball_key
```

Start by copying [.env.example](.env.example) and filling in the values.

## Layout

All Python source now lives under [src/](src) with tests in [tests/](tests). Install in editable mode or set `PYTHONPATH=src` when running scripts.


## Alchohalt

An experimental module for daily halt reminders and streak tracking.

```python
from alchohalt import checkin, metrics
checkin("halted")
print(metrics())
```

Command line helpers are also available:

```
python -m alchohalt.cli checkin halted --note "stayed on track"
python -m alchohalt.cli stats
python -m alchohalt.cli schedule 21:00
```

Run `python -m pytest tests/test_alchohalt.py` to verify basic streak logic.

## Development

Before committing, run the linters and test suite:

```bash
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
PYTHONPATH=src python -m pytest
python -m py_compile $(git ls-files '*.py')
```

