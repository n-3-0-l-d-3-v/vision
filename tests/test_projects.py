from __future__ import annotations

from vision.projects import list_projects
from vision.scaffold import scaffold_project


def test_list_projects_enumerates_multiple(tmp_path):
    scaffold_project("song-one", "music", root=tmp_path)
    scaffold_project("poster-one", "design", root=tmp_path)
    scaffold_project("secret-track", "music", private=True, root=tmp_path)

    projects = list_projects(root=tmp_path)
    names = {p["name"] for p in projects}
    assert names == {"song-one", "poster-one", "secret-track"}

    by_name = {p["name"]: p for p in projects}
    assert by_name["song-one"]["type"] == "music"
    assert by_name["poster-one"]["type"] == "design"
    assert by_name["secret-track"]["sensitivity_tier"] == "private"
    assert by_name["song-one"]["sensitivity_tier"] == "work"
    assert by_name["song-one"]["status"] == "active"


def test_list_projects_empty_root_returns_empty_list(tmp_path):
    assert list_projects(root=tmp_path / "does-not-exist") == []


def test_list_projects_skips_dirs_without_project_md(tmp_path):
    scaffold_project("real-project", "photo", root=tmp_path)
    (tmp_path / "random-folder").mkdir()
    (tmp_path / "random-folder" / "file.txt").write_text("x", encoding="utf-8")

    projects = list_projects(root=tmp_path)
    assert len(projects) == 1
    assert projects[0]["name"] == "real-project"
