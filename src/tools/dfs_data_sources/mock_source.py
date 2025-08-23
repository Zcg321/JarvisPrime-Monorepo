"""Mock DFS data source for tests.

MIT License.
Copyright (c) 2025 Zack
"""

def fetch_players():
    return [
        {"name": "A", "pos": "QB", "cost": 5000, "proj": 20},
        {"name": "B", "pos": "RB", "cost": 6000, "proj": 22},
        {"name": "C", "pos": "RB", "cost": 5500, "proj": 18},
        {"name": "D", "pos": "WR", "cost": 5000, "proj": 19},
        {"name": "E", "pos": "WR", "cost": 4800, "proj": 17},
        {"name": "F", "pos": "WR", "cost": 4700, "proj": 16},
        {"name": "G", "pos": "TE", "cost": 3000, "proj": 8},
    ]
