"""
Package containing automatically generated daily reflex modules.

Each module file is named with the date on which it was generated.  You can
iterate over ``__all__`` to inspect available modules.
"""

from importlib import import_module
from pathlib import Path
from typing import List

__all__: List[str] = []

_pkg_path = Path(__file__).resolve().parent
for mod_path in _pkg_path.glob("*_flame_reflex.py"):
    name = mod_path.stem
    __all__.append(name)

def load_module(name: str):
    """Import a daily module by its basename (without .py)."""
    return import_module(f"flame_prime.ai.daily_modules.{name}")
