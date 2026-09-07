from __future__ import annotations

import pytest

from vision.scaffold import (
    PROJECT_TYPES,
    SUBFOLDERS,
    ProjectExistsError,
    default_projects_root,
    project_dir,
    read_project_md,
    scaffold_project,
)


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
def test_scaffold_creates_folder_structure_for_every_type(tmp_path, project_type):
    result = scaffold_project(f"test-{project_type}", project_type, root=tmp_path)

    project_path = result["path"]
    assert project_path.is_dir()
    for sub in SUBFOLDERS:
        assert (project_path / sub).is_dir()
    assert (project_path / "project.md").is_file()


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
def test_scaffold_writes_correct_frontmatter(tmp_path, project_type):
    result = scaffold_project("my-project", project_type, root=tmp_path)

    fields = read_project_md(result["project_md_path"])
    assert fields["title"] == "my-project"
    assert fields["type"] == project_type
    assert fields["status"] == "active"
    assert fields["sensitivity_tier"] == "work"
    assert "created" in fields
    # created is a real ISO 8601 timestamp
    import datetime

    datetime.datetime.fromisoformat(fields["created"])


def test_scaffold_rejects_unknown_type(tmp_path):
    with pytest.raises(ValueError):
        scaffold_project("proj", "sculpture", root=tmp_path)


def test_scaffold_rejects_empty_name(tmp_path):
    with pytest.raises(ValueError):
        scaffold_project("   ", "music", root=tmp_path)


def test_scaffold_refuses_to_clobber_existing_project(tmp_path):
    scaffold_project("dup", "music", root=tmp_path)
    with pytest.raises(ProjectExistsError):
        scaffold_project("dup", "music", root=tmp_path)


def test_scaffold_body_has_expected_sections(tmp_path):
    result = scaffold_project("body-test", "writing", root=tmp_path)
    text = result["project_md_path"].read_text(encoding="utf-8")
    assert "## Overview" in text
    assert "## Notes" in text
    assert "## Decisions" in text
    assert "## Assets" in text


def test_project_dir_uses_root_override(tmp_path):
    d = project_dir("foo", root=tmp_path)
    assert d == tmp_path / "foo"


def test_default_projects_root_honors_env_var(monkeypatch, tmp_path):
    monkeypatch.setenv("VISION_PROJECTS_ROOT", str(tmp_path / "custom-root"))
    assert default_projects_root() == tmp_path / "custom-root"


def test_default_projects_root_falls_back_to_home_layout(monkeypatch):
    monkeypatch.delenv("VISION_PROJECTS_ROOT", raising=False)
    root = default_projects_root()
    assert root.name == "creative-projects"
    assert root.parent.name == "Neil"


def test_read_project_md_missing_file_returns_empty(tmp_path):
    assert read_project_md(tmp_path / "nope" / "project.md") == {}
