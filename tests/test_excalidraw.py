from __future__ import annotations

import json

from vision.excalidraw import REQUIRED_KEYS, SCHEMA_TYPE, is_valid_scene, new_scene, write_scene


def test_new_scene_has_required_top_level_keys():
    scene = new_scene("diagram")
    for key in REQUIRED_KEYS:
        assert key in scene
    assert scene["type"] == SCHEMA_TYPE
    assert isinstance(scene["elements"], list)
    assert scene["elements"] == []
    assert isinstance(scene["appState"], dict)
    assert "files" in scene
    assert scene["source"] == "https://excalidraw.com"


def test_new_scene_app_state_has_expected_defaults():
    scene = new_scene()
    assert scene["appState"]["viewBackgroundColor"] == "#ffffff"
    assert scene["appState"]["gridSize"] is None


def test_is_valid_scene_accepts_generated_scene():
    assert is_valid_scene(new_scene("x")) is True


def test_is_valid_scene_rejects_missing_keys():
    scene = new_scene("x")
    del scene["appState"]
    assert is_valid_scene(scene) is False


def test_is_valid_scene_rejects_wrong_type_field():
    scene = new_scene("x")
    scene["type"] = "not-excalidraw"
    assert is_valid_scene(scene) is False


def test_is_valid_scene_rejects_non_dict():
    assert is_valid_scene(["not", "a", "dict"]) is False


def test_write_scene_produces_parseable_json_file(tmp_path):
    path = write_scene(tmp_path / "demo-diagram", name="demo-diagram")

    assert path.exists()
    assert path.suffix == ".excalidraw"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert is_valid_scene(data)


def test_write_scene_does_not_double_suffix(tmp_path):
    path = write_scene(tmp_path / "demo.excalidraw")
    assert path.name == "demo.excalidraw"


def test_write_scene_creates_parent_dirs(tmp_path):
    target = tmp_path / "nested" / "dir" / "diagram"
    path = write_scene(target)
    assert path.exists()
    assert path.parent.is_dir()
