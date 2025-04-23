# === JARVIS PRIME MAIN BOOTSTRAP ===

import os, sys

# === PATH SETUP ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_PATH = os.path.join(CURRENT_DIR)
sys.path.append(CORE_PATH)

# === CORE MODULES ===
from evolution_handler import handle_evolution
from goal_pathfinder_handler import resolve_path

if __name__ == "__main__":
    print("Jarvis Prime system initializing...")
    handle_evolution()
    resolve_path()