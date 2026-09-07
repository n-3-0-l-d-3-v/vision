from __future__ import annotations

import json
import time

from vision.assets import build_manifest, render_markdown, write_manifest


def _make_project(tmp_path):
    project = tmp_path / "proj"
    (project / "assets").mkdir(parents=True)
    (project / "exports").mkdir(parents=True)
    (project / "drafts").mkdir(parents=True)

    (project / "assets" / "sketch.png").write_bytes(b"\x89PNG-fake-bytes")
    (project / "assets" / "notes.txt").write_text("hello", encoding="utf-8")
    (project / "exports" / "final.mp4").write_bytes(b"0" * 1024)
    # drafts/ should NOT show up in the manifest
    (project / "drafts" / "wip.txt").write_text("wip", encoding="utf-8")

    return project


def test_build_manifest_lists_assets_and_exports_not_drafts(tmp_path):
    project = _make_project(tmp_path)
    entries = build_manifest(project)

    names = {e["name"] for e in entries}
    assert names == {"sketch.png", "notes.txt", "final.mp4"}
    assert "wip.txt" not in names


def test_build_manifest_entries_have_expected_fields(tmp_path):
    project = _make_project(tmp_path)
    entries = build_manifest(project)

    by_name = {e["name"]: e for e in entries}
    png = by_name["sketch.png"]
    assert png["type"] == "png"
    assert png["folder"] == "assets"
    assert png["size_bytes"] == len(b"\x89PNG-fake-bytes")
    assert "modified" in png
    import datetime

    datetime.datetime.fromisoformat(png["modified"])

    mp4 = by_name["final.mp4"]
    assert mp4["folder"] == "exports"
    assert mp4["size_bytes"] == 1024


def test_build_manifest_missing_scan_dirs_returns_empty(tmp_path):
    empty_project = tmp_path / "empty"
    empty_project.mkdir()
    assert build_manifest(empty_project) == []


def test_render_markdown_contains_table_rows(tmp_path):
    project = _make_project(tmp_path)
    entries = build_manifest(project)
    md = render_markdown(entries, project_name="proj")

    assert "sketch.png" in md
    assert "final.mp4" in md
    assert "| Name | Folder | Type | Size (bytes) | Modified |" in md


def test_render_markdown_no_files():
    md = render_markdown([], project_name="empty")
    assert "No files found" in md


def test_write_manifest_json(tmp_path):
    project = _make_project(tmp_path)
    out = write_manifest(project, fmt="json")

    assert out.name == "vision-assets-manifest.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 3
    names = {e["name"] for e in data}
    assert names == {"sketch.png", "notes.txt", "final.mp4"}


def test_write_manifest_markdown(tmp_path):
    project = _make_project(tmp_path)
    out = write_manifest(project, fmt="md")

    assert out.name == "vision-assets-manifest.md"
    text = out.read_text(encoding="utf-8")
    assert "sketch.png" in text


def test_write_manifest_rejects_bad_format(tmp_path):
    import pytest

    project = _make_project(tmp_path)
    with pytest.raises(ValueError):
        write_manifest(project, fmt="xml")
