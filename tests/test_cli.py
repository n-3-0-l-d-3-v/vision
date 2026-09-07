from __future__ import annotations

import json

from click.testing import CliRunner

from vision.cli import cli


def test_health_flag_prints_json_and_exits_zero_when_healthy(tmp_path, monkeypatch):
    monkeypatch.setenv("VISION_PROJECTS_ROOT", str(tmp_path / "creative-projects"))
    runner = CliRunner()
    result = runner.invoke(cli, ["--health"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["healthy"] is True
    assert "version" in payload
    assert payload["projects_root"] == str(tmp_path / "creative-projects")


def test_health_flag_output_shape():
    runner = CliRunner()
    result = runner.invoke(cli, ["--health"])
    payload = json.loads(result.output)
    for key in ("version", "healthy", "projects_root", "projects_root_reachable", "vault_writable", "vault_error"):
        assert key in payload


def test_no_args_prints_help():
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Vision" in result.output


def test_new_command_end_to_end(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["new", "cli-song", "--type", "music", "--root", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "cli-song" / "project.md").is_file()
    assert (tmp_path / "cli-song" / "assets").is_dir()
    assert "Created project" in result.output


def test_new_command_rejects_bad_type(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["new", "bad", "--type", "sculpture", "--root", str(tmp_path)]
    )
    assert result.exit_code != 0


def test_new_command_duplicate_fails(tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["new", "dup", "--type", "music", "--root", str(tmp_path)])
    result = runner.invoke(cli, ["new", "dup", "--type", "music", "--root", str(tmp_path)])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_excalidraw_command_writes_valid_file(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["excalidraw", "demo-diagram"])
        assert result.exit_code == 0, result.output
        from pathlib import Path

        out = Path("demo-diagram.excalidraw")
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["type"] == "excalidraw"


def test_assets_command_lists_files(tmp_path):
    project = tmp_path / "proj"
    (project / "assets").mkdir(parents=True)
    (project / "assets" / "img.png").write_bytes(b"data")

    runner = CliRunner()
    result = runner.invoke(cli, ["assets", str(project)])
    assert result.exit_code == 0, result.output
    assert "img.png" in result.output
    assert (project / "vision-assets-manifest.md").is_file()


def test_list_command_enumerates_projects(tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["new", "proj-a", "--type", "music", "--root", str(tmp_path)])
    runner.invoke(cli, ["new", "proj-b", "--type", "design", "--root", str(tmp_path)])

    result = runner.invoke(cli, ["list", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "proj-a" in result.output
    assert "proj-b" in result.output


def test_list_command_json(tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["new", "proj-c", "--type", "video", "--root", str(tmp_path)])

    result = runner.invoke(cli, ["list", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert len(payload["projects"]) == 1
    assert payload["projects"][0]["name"] == "proj-c"


def test_list_command_empty_root(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--root", str(tmp_path / "nope")])
    assert result.exit_code == 0
    assert "No projects found" in result.output


def test_new_command_private_flag_routes_moc_to_private(tmp_path, monkeypatch):
    # Point Vision's vault root at a temp dir by monkeypatching cli._vault_root
    import vision.cli as cli_module

    vault_root = tmp_path / "vault" / "Vision"
    monkeypatch.setattr(cli_module, "_vault_root", lambda: vault_root)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["new", "private-song", "--type", "music", "--private", "--root", str(tmp_path / "projects")],
    )
    assert result.exit_code == 0, result.output
    assert (vault_root / "private" / "private-song.md").is_file()
    assert not (vault_root / "private-song.md").exists()
