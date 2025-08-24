import json
from pathlib import Path
import html

def main() -> None:
    src = Path("logs/reports/savepoint_timeline.json")
    out = Path("artifacts/reports/savepoints.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(src.read_text()) if src.exists() else []
    lines = [
        "<html><head><meta charset='utf-8'><style>body{font-family:sans-serif;}table{border-collapse:collapse;}td,th{border:1px solid #ccc;padding:4px;}</style></head><body>",
        "<h1>Savepoints</h1>",
        "<table><tr><th>ts</th><th>event</th></tr>",
    ]
    for item in data:
        ts = html.escape(str(item.get("ts")))
        ev = html.escape(str(item.get("event")))
        lines.append(f"<tr><td>{ts}</td><td>{ev}</td></tr>")
    lines.append("</table></body></html>")
    out.write_text("\n".join(lines))
    print(str(out))

if __name__ == "__main__":
    main()
