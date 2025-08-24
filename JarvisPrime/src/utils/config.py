"""Central place to load API keys and secrets.

Secrets are read from environment variables, optionally populated by a
``.env`` file loaded via ``python-dotenv``. Copy ``.env.example`` to ``.env``
and fill in the values to provide credentials during development.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv


load_dotenv()

BALLEDONTLIE_API_KEY: str = os.getenv("BALLEDONTLIE_API_KEY", "")
ODDS_RAPIDAPI_KEY: str = os.getenv("ODDS_RAPIDAPI_KEY", "")
THE_ODDS_API_KEY: str = os.getenv("THE_ODDS_API_KEY", "")
API_FOOTBALL_KEY: str = os.getenv("API_FOOTBALL_KEY", "")

# add more as needed
