"""Text -> Excalidraw diagram (`vision diagram`).

Two ways in:
  * natural language ("a client calls an API gateway which fans out to ..."):
    the LOCAL model (Ollama, schema-forced JSON) extracts only boxes and
    arrows -- it never draws anything;
  * an edge list ("Client -> Gateway: HTTPS, Gateway -> Auth"): parsed
    deterministically, no model needed.

Layout and rendering are plain code: a left-to-right layered layout and
fully-formed Excalidraw elements (bound labels, arrows bound to boxes), so the
output always opens cleanly and looks tidy regardless of what the model said.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Optional

from vision.excalidraw import new_scene

OLLAMA = "http://127.0.0.1:11434"
MODEL = "qwen2.5:7b"
MAX_NODES = 30
BOX_W, BOX_H, COL_GAP, ROW_GAP = 200, 80, 120, 60

_GRAPH_SCHEMA = {
    "type": "object",
    "properties": {
        "nodes": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"}, "label": {"type": "string"}}, "required": ["id", "label"]}},
        "edges": {"type": "array", "items": {"type": "object", "properties": {
            "from": {"type": "string"}, "to": {"type": "string"}, "label": {"type": "string"}},
            "required": ["from", "to"]}},
    },
    "required": ["nodes", "edges"],
}


class DiagramError(Exception):
    pass


# ---------------------------------------------------------------- graph in --

def parse_edges(text: str) -> dict:
    """'A -> B: label, B -> C' (commas, semicolons or newlines) -> graph."""
    nodes: dict[str, str] = {}
    edges = []
    for part in re.split(r"[\n;,]+", text):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"(.+?)\s*-+>\s*(.+?)(?:\s*:\s*(.+))?$", part)
        if not m:
            nodes.setdefault(_key(part), part)
            continue
        a, b, label = (x.strip() if x else x for x in m.groups())
        nodes.setdefault(_key(a), a)
        nodes.setdefault(_key(b), b)
        edges.append({"from": _key(a), "to": _key(b), "label": label or ""})
    return {"nodes": [{"id": k, "label": v} for k, v in nodes.items()], "edges": edges}


def extract_graph(description: str, model: str = MODEL, host: str = OLLAMA) -> dict:
    prompt = (
        "Extract the components and connections from this description as a diagram. "
        "Nodes are the things (services, people, steps, data stores); edges are directed "
        "arrows between node ids with an optional short label. Use short labels (max 4 words). "
        "Only include what the description states.\n\nDescription: " + description
    )
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "format": _GRAPH_SCHEMA, "stream": False,
                       "options": {"temperature": 0.1}}).encode()
    req = urllib.request.Request(f"{host}/api/chat", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            return json.loads(json.loads(r.read())["message"]["content"])
    except Exception as exc:  # noqa: BLE001
        raise DiagramError(f"local model unavailable ({exc}); use an edge list like 'A -> B, B -> C'") from exc


def _key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "node"


def clean_graph(g: dict) -> dict:
    """Dedupe/trim nodes, drop edges to unknown nodes and self-loops, cap size."""
    nodes: dict[str, str] = {}
    for n in g.get("nodes") or []:
        nid = _key(str(n.get("id") or n.get("label") or ""))
        label = str(n.get("label") or n.get("id") or "").strip()[:60]
        if label and nid not in nodes and len(nodes) < MAX_NODES:
            nodes[nid] = label
    edges, seen = [], set()
    for e in g.get("edges") or []:
        a, b = _key(str(e.get("from", ""))), _key(str(e.get("to", "")))
        if a in nodes and b in nodes and a != b and (a, b) not in seen:
            seen.add((a, b))
            edges.append({"from": a, "to": b, "label": str(e.get("label") or "").strip()[:40]})
    if not nodes:
        raise DiagramError("no components found to draw")
    return {"nodes": [{"id": k, "label": v} for k, v in nodes.items()], "edges": edges}


# ------------------------------------------------------------------ layout --

def layout(g: dict) -> dict[str, tuple[float, float]]:
    """Layered left-to-right layout: column = longest path from a source
    (back edges of cycles ignored), rows centred per column."""
    ids = [n["id"] for n in g["nodes"]]
    out_edges = defaultdict(list)
    for e in g["edges"]:
        out_edges[e["from"]].append(e["to"])

    # drop back edges with a DFS so the graph is acyclic for layering
    state: dict[str, int] = {}
    dag = defaultdict(list)

    def dfs(u):
        state[u] = 1
        for v in out_edges[u]:
            if state.get(v) == 1:
                continue  # back edge
            dag[u].append(v)
            if v not in state:
                dfs(v)
        state[u] = 2

    for u in ids:
        if u not in state:
            dfs(u)

    level = {u: 0 for u in ids}
    order = _topo(ids, dag)
    for u in order:
        for v in dag[u]:
            level[v] = max(level[v], level[u] + 1)

    cols = defaultdict(list)
    for u in ids:
        cols[level[u]].append(u)
    tallest = max(len(c) for c in cols.values())
    pos = {}
    for c, members in cols.items():
        offset = (tallest - len(members)) * (BOX_H + ROW_GAP) / 2
        for r, u in enumerate(members):
            pos[u] = (c * (BOX_W + COL_GAP), offset + r * (BOX_H + ROW_GAP))
    return pos


def _topo(ids, dag):
    indeg = {u: 0 for u in ids}
    for u in ids:
        for v in dag[u]:
            indeg[v] += 1
    queue = [u for u in ids if indeg[u] == 0]
    out = []
    while queue:
        u = queue.pop(0)
        out.append(u)
        for v in dag[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return out


# --------------------------------------------------------------- rendering --

def _seed(*parts) -> int:
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def _base(eid: str, etype: str, x, y, w, h, **extra) -> dict:
    el = {
        "id": eid, "type": etype, "x": x, "y": y, "width": w, "height": h, "angle": 0,
        "strokeColor": "#1e1e1e", "backgroundColor": "transparent", "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None, "seed": _seed(eid, "s"),
        "version": 1, "versionNonce": _seed(eid, "n"), "isDeleted": False,
        "boundElements": [], "updated": 1, "link": None, "locked": False,
    }
    el.update(extra)
    return el


def _text(eid, text, x, y, w, h, container=None, size=20) -> dict:
    return _base(eid, "text", x, y, w, h, text=text, fontSize=size, fontFamily=1,
                 textAlign="center", verticalAlign="middle", containerId=container,
                 originalText=text, lineHeight=1.25, autoResize=True)


def render(g: dict, pos: dict[str, tuple[float, float]]) -> list[dict]:
    els: dict[str, dict] = {}
    palette = ["#a5d8ff", "#b2f2bb", "#ffec99", "#ffc9c9", "#d0bfff", "#99e9f2"]
    for i, n in enumerate(g["nodes"]):
        x, y = pos[n["id"]]
        box_id, txt_id = f"box_{n['id']}", f"txt_{n['id']}"
        els[box_id] = _base(box_id, "rectangle", x, y, BOX_W, BOX_H,
                            backgroundColor=palette[i % len(palette)], roundness={"type": 3},
                            boundElements=[{"type": "text", "id": txt_id}])
        els[txt_id] = _text(txt_id, n["label"], x + 10, y + BOX_H / 2 - 12, BOX_W - 20, 25, container=box_id)
    for e in g["edges"]:
        (ax, ay), (bx, by) = pos[e["from"]], pos[e["to"]]
        sx, sy = ax + BOX_W, ay + BOX_H / 2
        if bx <= ax:  # same or earlier column: leave from the bottom, enter from the top
            sx, sy = ax + BOX_W / 2, ay + BOX_H
            ex, ey = bx + BOX_W / 2, by
        else:
            ex, ey = bx, by + BOX_H / 2
        arrow_id = f"arr_{e['from']}_{e['to']}"
        arrow = _base(arrow_id, "arrow", sx, sy, abs(ex - sx), abs(ey - sy),
                      points=[[0, 0], [ex - sx, ey - sy]], lastCommittedPoint=None,
                      startBinding={"elementId": f"box_{e['from']}", "focus": 0, "gap": 4},
                      endBinding={"elementId": f"box_{e['to']}", "focus": 0, "gap": 4},
                      startArrowhead=None, endArrowhead="arrow", roundness={"type": 2})
        els[arrow_id] = arrow
        for end in (e["from"], e["to"]):
            els[f"box_{end}"]["boundElements"].append({"type": "arrow", "id": arrow_id})
        if e["label"]:
            lid = f"lbl_{e['from']}_{e['to']}"
            arrow["boundElements"].append({"type": "text", "id": lid})
            els[lid] = _text(lid, e["label"], (sx + ex) / 2 - 50, (sy + ey) / 2 - 20, 100, 20,
                             container=arrow_id, size=14)
    return list(els.values())


def build_scene(g: dict) -> dict:
    g = clean_graph(g)
    scene = new_scene()
    scene["elements"] = render(g, layout(g))
    return scene


def write_diagram(path: Path, g: dict) -> Path:
    if path.suffix != ".excalidraw":
        path = path.with_name(path.name + ".excalidraw")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_scene(g), indent=2), encoding="utf-8")
    return path


def graph_from_input(text: str, model: Optional[str] = None) -> dict:
    """Edge-list syntax is parsed offline; anything else goes to the local model."""
    if "->" in text:
        return parse_edges(text)
    return extract_graph(text, model or MODEL)
