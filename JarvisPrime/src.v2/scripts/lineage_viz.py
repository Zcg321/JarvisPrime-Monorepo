import json
from pathlib import Path


def main():
    sp_dir = Path("logs/savepoints")
    nodes = {}
    edges = []
    for fp in sorted(sp_dir.glob("*.json")):
        try:
            data = json.loads(fp.read_text())
        except Exception:
            continue
        lid = data.get("lineage_id")
        parent = data.get("parent_id")
        tool = data.get("event")
        if lid:
            nodes[lid] = tool
        if lid and parent:
            edges.append((parent, lid))
    rep_dir = Path("artifacts/reports")
    rep_dir.mkdir(parents=True, exist_ok=True)
    dot_path = rep_dir / "lineage.dot"
    with dot_path.open("w") as f:
        f.write("digraph G {\n")
        groups = {}
        for lid, tool in nodes.items():
            groups.setdefault(tool, []).append(lid)
        for i, (tool, ids) in enumerate(groups.items()):
            f.write(f"  subgraph cluster_{i} {{ label=\"{tool}\";\n")
            for nid in ids:
                f.write(f"    \"{nid}\";\n")
            f.write("  }\n")
        for p, c in edges:
            f.write(f"  \"{p}\" -> \"{c}\";\n")
        f.write("}\n")
    html_path = rep_dir / "lineage.html"
    with html_path.open("w") as f:
        f.write("<html><body><pre>\n")
        f.write(dot_path.read_text())
        f.write("\n</pre></body></html>")


if __name__ == "__main__":
    main()
