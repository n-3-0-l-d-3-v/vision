from __future__ import annotations

from vision.frontmatter import parse
from vision.vault import PRIVATE_SUBDIR, append_note, moc_path, write_project_moc


def test_public_project_moc_goes_to_default_vault_root(tmp_path):
    vault_root = tmp_path / "vault" / "Vision"
    path = write_project_moc("My Song", "music", private=False, vault_root=vault_root)

    assert path.parent == vault_root
    assert path.is_file()


def test_private_project_moc_routes_to_private_subpath(tmp_path):
    vault_root = tmp_path / "vault" / "Vision"
    path = write_project_moc("Secret Album", "music", private=True, vault_root=vault_root)

    assert path.parent == vault_root / PRIVATE_SUBDIR
    assert PRIVATE_SUBDIR in path.parts
    assert path.is_file()


def test_private_flag_sets_frontmatter_tier_private(tmp_path):
    vault_root = tmp_path / "vault" / "Vision"
    path = write_project_moc("Secret Album", "music", private=True, vault_root=vault_root)

    fields, _ = parse(path.read_text(encoding="utf-8"))
    assert fields["sensitivity_tier"] == "private"


def test_public_flag_sets_frontmatter_tier_work(tmp_path):
    vault_root = tmp_path / "vault" / "Vision"
    path = write_project_moc("Public Piece", "design", private=False, vault_root=vault_root)

    fields, _ = parse(path.read_text(encoding="utf-8"))
    assert fields["sensitivity_tier"] == "work"


def test_moc_path_is_pure_function_of_inputs(tmp_path):
    vault_root = tmp_path / "vault" / "Vision"
    pub = moc_path("Some Name!!", private=False, vault_root=vault_root)
    priv = moc_path("Some Name!!", private=True, vault_root=vault_root)

    assert pub == vault_root / "some-name.md"
    assert priv == vault_root / PRIVATE_SUBDIR / "some-name.md"


def test_moc_body_records_type_and_status(tmp_path):
    vault_root = tmp_path / "vault" / "Vision"
    path = write_project_moc("Body Test", "video", status="active", private=False, vault_root=vault_root)
    text = path.read_text(encoding="utf-8")
    assert "video" in text
    assert "## Notes" in text
    assert "## Decisions" in text


def test_append_note_inserts_under_existing_heading(tmp_path):
    vault_root = tmp_path / "vault" / "Vision"
    path = write_project_moc("Append Test", "design", private=False, vault_root=vault_root)

    append_note(path, "Decisions", "Chose blue palette.")
    text = path.read_text(encoding="utf-8")
    assert "Chose blue palette." in text
    # Ends up under the Decisions heading, not appended at end of file
    decisions_idx = text.index("## Decisions")
    note_idx = text.index("Chose blue palette.")
    assert note_idx > decisions_idx


def test_append_note_creates_heading_if_missing(tmp_path):
    vault_root = tmp_path / "vault" / "Vision"
    path = write_project_moc("Append Test 2", "design", private=False, vault_root=vault_root)

    append_note(path, "Ideas", "Try a grid layout.")
    text = path.read_text(encoding="utf-8")
    assert "## Ideas" in text
    assert "Try a grid layout." in text


def test_append_note_missing_file_raises(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        append_note(tmp_path / "nope.md", "Notes", "text")
