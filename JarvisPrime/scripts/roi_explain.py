import json
import os
from pathlib import Path

from src.tools import roi_cohorts

ATTRIB_LOG = Path(os.environ.get("ROI_ATTRIB_LOG", "logs/reports/roi_attrib.jsonl"))
OUT_JSON = Path("artifacts/reports/roi_explain.json")
OUT_HTML = Path("artifacts/reports/roi_explain.html")


def build() -> dict:
    cohorts = roi_cohorts.roi_cohorts({"lookback_days": 90, "group_by": ["slate_type"]})
    players = {}
    if ATTRIB_LOG.exists():
        with ATTRIB_LOG.open() as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    for p in rec.get("result", {}).get("players", []):
                        pid = p.get("player_id")
                        players[pid] = players.get(pid, 0.0) + float(p.get("mc", 0.0))
                except Exception:
                    continue
    top_players = [{"player_id": pid, "mc": players[pid]} for pid in sorted(players)]
    data = {"cohorts": cohorts, "players": top_players}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, indent=2))
    html = ["<html><body><h1>Cohorts</h1><ul>"]
    for c in cohorts:
        html.append(f"<li>{json.dumps(c)}</li>")
    html.append("</ul><h1>Players</h1><ul>")
    for p in top_players:
        html.append(f"<li>{p['player_id']}:{p['mc']}</li>")
    html.append("</ul></body></html>")
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text("".join(html))
    return data


def main() -> None:  # pragma: no cover
    build()


if __name__ == "__main__":  # pragma: no cover
    main()
