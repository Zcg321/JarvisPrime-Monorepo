import json
from pathlib import Path


def main() -> None:
    sp_dir = Path("logs/savepoints")
    nodes = []
    links = []
    for p in sorted(sp_dir.glob("*.json")):
        data = json.loads(p.read_text())
        lid = data.get("lineage_id")
        parent = data.get("parent_id")
        tool = data.get("event")
        if lid:
            nodes.append({"id": lid, "tool": tool})
            if parent:
                links.append({"source": parent, "target": lid})
    rep_dir = Path("artifacts/reports")
    rep_dir.mkdir(parents=True, exist_ok=True)
    html = rep_dir / "lineage_ui.html"
    html.write_text(
        "<html><body><svg id='g' width='600' height='400'></svg>"
        f"<script>const data={{nodes:{json.dumps(nodes)},links:{json.dumps(links)}}};" \
        "const svg=document.getElementById('g');"
        "data.nodes.forEach((n,i)=>{const c=document.createElementNS('http://www.w3.org/2000/svg','circle');c.setAttribute('cx',50+i*30);c.setAttribute('cy',200);c.setAttribute('r',10);c.setAttribute('data-tool',n.tool);c.title=n.id;svg.appendChild(c);});" \
        "data.links.forEach(l=>{const line=document.createElementNS('http://www.w3.org/2000/svg','line');line.setAttribute('x1',50+data.nodes.findIndex(n=>n.id==l.source)*30);line.setAttribute('y1',200);line.setAttribute('x2',50+data.nodes.findIndex(n=>n.id==l.target)*30);line.setAttribute('y2',200);line.setAttribute('stroke','#999');svg.appendChild(line);});" \
        "</script></body></html>"
    )


if __name__ == "__main__":
    main()

