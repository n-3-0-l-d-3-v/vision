import json

import pytest

from vision import diagram
from vision.excalidraw import is_valid_scene


def test_parse_edges_with_labels():
    g = diagram.parse_edges("Client -> API Gateway: HTTPS, API Gateway -> Auth; API Gateway -> Orders DB")
    assert {n["label"] for n in g["nodes"]} == {"Client", "API Gateway", "Auth", "Orders DB"}
    assert {"from": "client", "to": "api_gateway", "label": "HTTPS"} in g["edges"]


def test_clean_graph_drops_bad_edges_and_dupes():
    g = diagram.clean_graph({"nodes": [{"id": "a", "label": "A"}, {"id": "a", "label": "dup"}, {"id": "b", "label": "B"}],
                             "edges": [{"from": "a", "to": "b"}, {"from": "a", "to": "b"}, {"from": "a", "to": "zzz"}, {"from": "b", "to": "b"}]})
    assert len(g["nodes"]) == 2 and g["edges"] == [{"from": "a", "to": "b", "label": ""}]


def test_empty_graph_rejected():
    with pytest.raises(diagram.DiagramError):
        diagram.clean_graph({"nodes": [], "edges": []})


def test_layout_is_left_to_right_and_survives_cycles():
    g = diagram.parse_edges("A -> B, B -> C, C -> A, A -> D")
    pos = diagram.layout(diagram.clean_graph(g))
    assert pos["a"][0] < pos["b"][0] < pos["c"][0]
    assert pos["d"][0] > pos["a"][0]


def test_scene_is_valid_and_bindings_are_consistent(tmp_path):
    g = diagram.parse_edges("Client -> Gateway: HTTPS, Gateway -> Auth, Gateway -> DB")
    path = diagram.write_diagram(tmp_path / "arch", g)
    scene = json.loads(path.read_text(encoding="utf-8"))
    assert path.suffix == ".excalidraw" and is_valid_scene(scene)
    els = {e["id"]: e for e in scene["elements"]}
    for e in els.values():
        if e["type"] == "arrow":
            for b in (e["startBinding"], e["endBinding"]):
                assert b["elementId"] in els
                assert {"type": "arrow", "id": e["id"]} in els[b["elementId"]]["boundElements"]
        if e["type"] == "text" and e["containerId"]:
            assert {"type": "text", "id": e["id"]} in els[e["containerId"]]["boundElements"]


def test_output_is_deterministic(tmp_path):
    g = diagram.parse_edges("A -> B, B -> C")
    a = diagram.write_diagram(tmp_path / "x", g).read_text()
    b = diagram.write_diagram(tmp_path / "y", g).read_text()
    assert a == b


def test_natural_language_without_model_gives_clear_error(monkeypatch):
    monkeypatch.setattr(diagram, "OLLAMA", "http://127.0.0.1:1")
    with pytest.raises(diagram.DiagramError, match="edge list"):
        diagram.extract_graph("a client talks to a server", host="http://127.0.0.1:1")
