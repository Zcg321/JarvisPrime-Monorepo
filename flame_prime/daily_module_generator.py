"""Flame Prime: Daily Reflex Module Generator
----------------------------------------

This script is intended to be run once per day via a scheduler (for example, a
GitHub Actions workflow).  On each invocation it creates a new Python module
under ``flame_prime/ai/daily_modules`` with a name based on the current date.
The generated module defines a ``council_weights`` dictionary and an
``apply_daily_weights`` function which applies these weights to a metrics
dictionary.  The weights are randomly perturbed around 1.0 to introduce
variation into each day's reflex logic.  A history of generated modules can
be used to compare how the system evolves over time.

Usage: ``python flame_prime/daily_module_generator.py``

The script can be run manually or triggered on a schedule via GitHub
Actions.  See ``.github/workflows/daily_module_generation.yml`` for an
example workflow configuration.
"""

import os
import random
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.join(BASE_DIR, "ai", "daily_modules")

def ensure_modules_dir_exists() -> None:
    """Ensure that the target directory exists before writing files."""
    if not os.path.exists(MODULES_DIR):
        os.makedirs(MODULES_DIR, exist_ok=True)

def generate_weights() -> dict:
    """Generate a random set of council weights."""
    return {
        "goku": round(random.uniform(0.95, 1.10), 3),
        "gohan": round(random.uniform(0.95, 1.10), 3),
        "vegeta": round(random.uniform(0.95, 1.10), 3),
        "piccolo": round(random.uniform(0.90, 1.05), 3),
    }

def generate_module_contents(weights: dict) -> str:
    """Construct the Python source code for a daily module."""
    lines = []
    lines.append('"""Generated Daily Reflex Module\n'
                 'This module is automatically generated each day by Flame Prime. '
                 'It defines a set of council weights and an apply_daily_weights helper '
                 'for applying those weights to a metrics dictionary.\n'
                 '"""')
    lines.append(f"council_weights = {weights}\n")
    lines.append(
        "def apply_daily_weights(metrics: dict) -> dict:\n"
        "    \"\"\"Apply the daily council weights to a metrics dictionary.\"\"\"\n"
        "    updated = metrics.copy()\n"
        "    updated['profitability'] *= council_weights['goku']\n"
        "    updated['consistency'] *= council_weights['gohan']\n"
        "    updated['edge_discovery'] *= council_weights['vegeta']\n"
        "    if 'variance' in updated:\n"
        "        updated['variance'] *= council_weights['piccolo']\n"
        "    return updated\n"
    )
    return '\n'.join(lines)

def generate_module() -> str:
    """
    Generate a new daily reflex module file.

    The module filename is based on the current date in UTC.  If a module
    already exists for today, the script will not overwrite it but will
    return the path to the existing file instead.

    Returns:
        str: The path to the generated (or existing) module file.
    """
    ensure_modules_dir_exists()
    today = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    filename = f"{today}_flame_reflex.py"
    filepath = os.path.join(MODULES_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    weights = generate_weights()
    code = generate_module_contents(weights)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
    return filepath

def main() -> None:
    path = generate_module()
    print(f"[FlamePrime] Generated daily reflex module at: {path}")

if __name__ == "__main__":
    main()
