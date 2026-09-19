"""Vision CLI.

`vision --health` is an eager top-level flag (not a subcommand), matching
Friday (`friday --health`), Ultron (`ultron --health`), Jarvis
(`jarvis --health`), and Wall-E (`wall-e --health`) -- see README.md and
agent.yaml.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from vision import __version__
from vision.assets import build_manifest, render_markdown as render_manifest_markdown, write_manifest
from vision.excalidraw import write_scene
from vision.projects import list_projects
from vision.scaffold import PROJECT_TYPES, ProjectExistsError, default_projects_root, scaffold_project
from vision.vault import write_project_moc


def _print_json(data: dict) -> None:
    click.echo(json.dumps(data, indent=2, default=str))


def _vault_root() -> Path:
    """Vision's own vault root: `<repo>/vault/Vision/`, matching
    agent.yaml's `vault_write_path`."""
    import os
    shared = os.environ.get("VAULT_PATH")
    if shared:
        return Path(shared) / "agents" / "Vision"
    return Path(__file__).resolve().parents[1] / "vault" / "Vision"


def _self_health() -> dict:
    """Vision's own health: can it locate its projects root's parent
    (i.e. the root either exists or its parent does, so it *could* be
    created) and write to its own vault directory. No network calls, no
    dependency on any creative app being installed."""
    root = default_projects_root()
    root_reachable = root.exists() or root.parent.exists()

    vault_dir = _vault_root()
    vault_writable = True
    vault_error = None
    try:
        vault_dir.mkdir(parents=True, exist_ok=True)
        probe = vault_dir / ".health_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        vault_writable = False
        vault_error = str(exc)

    healthy = root_reachable and vault_writable
    return {
        "version": __version__,
        "healthy": healthy,
        "projects_root": str(root),
        "projects_root_reachable": root_reachable,
        "vault_writable": vault_writable,
        "vault_error": vault_error,
    }


@click.group(invoke_without_command=True)
@click.option(
    "--health",
    "show_health",
    is_flag=True,
    default=False,
    help="Print Vision's own JSON health report and exit. This is the "
    "ecosystem agent contract's health_check_command -- see agent.yaml.",
)
@click.version_option(__version__, prog_name="vision")
@click.pass_context
def cli(ctx: click.Context, show_health: bool) -> None:
    """Vision: creative and ideation agent."""
    if show_health:
        payload = _self_health()
        _print_json(payload)
        ctx.exit(0 if payload["healthy"] else 1)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(name="new")
@click.argument("name")
@click.option(
    "--type",
    "project_type",
    type=click.Choice(PROJECT_TYPES),
    required=True,
    help="Creative project category.",
)
@click.option(
    "--private",
    is_flag=True,
    default=False,
    help="Mark this project's sensitivity tier as private (default: work) "
    "and route its vault MOC note to vault/Vision/private/ instead of "
    "vault/Vision/.",
)
@click.option(
    "--root",
    "root_raw",
    default=None,
    help="Override the projects root (default: $VISION_PROJECTS_ROOT or "
    "~/Desktop/Neil/creative-projects).",
)
def new_cmd(name: str, project_type: str, private: bool, root_raw: Optional[str]) -> None:
    """Scaffold a new creative project: folder structure, project.md, and a vault MOC note."""
    root = Path(root_raw) if root_raw else None
    try:
        result = scaffold_project(name, project_type, private=private, root=root)
    except ProjectExistsError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    moc_path = write_project_moc(
        name,
        project_type,
        status=result["status"],
        private=private,
        project_path=result["path"],
        vault_root=_vault_root(),
    )

    click.echo(f"Created project: {result['path']}")
    click.echo(f"  project.md: {result['project_md_path']}")
    click.echo(f"  sensitivity tier: {result['sensitivity_tier']}")
    click.echo(f"  vault MOC note: {moc_path}")


@cli.command(name="excalidraw")
@click.argument("name")
@click.option(
    "--project",
    "project_dir_raw",
    default=None,
    help="Project directory to write into (writes to <project>/assets/<name>.excalidraw). "
    "Default: write <name>.excalidraw to the current directory.",
)
def excalidraw_cmd(name: str, project_dir_raw: Optional[str]) -> None:
    """Generate a blank, schema-valid .excalidraw starter file."""
    if project_dir_raw:
        target = Path(project_dir_raw) / "assets" / name
    else:
        target = Path.cwd() / name

    path = write_scene(target, name=name)
    click.echo(f"Created: {path}")


@cli.command(name="assets")
@click.argument("project_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "md"]),
    default="md",
    help="Manifest output format.",
)
@click.option(
    "--no-write",
    "no_write",
    is_flag=True,
    default=False,
    help="Don't write the manifest file, just print it.",
)
def assets_cmd(project_dir: str, fmt: str, no_write: bool) -> None:
    """Catalog a creative project's assets/ and exports/ folders into a manifest."""
    target = Path(project_dir)
    entries = build_manifest(target)

    written_path: Optional[Path] = None
    if not no_write:
        written_path = write_manifest(target, fmt=fmt)

    if fmt == "json":
        _print_json({"project_dir": str(target), "entries": entries, "written_to": str(written_path) if written_path else None})
    else:
        click.echo(render_manifest_markdown(entries, project_name=target.name))
        if written_path:
            click.echo(f"\nWritten to: {written_path}")


@cli.command(name="list")
@click.option(
    "--root",
    "root_raw",
    default=None,
    help="Override the projects root (default: $VISION_PROJECTS_ROOT or "
    "~/Desktop/Neil/creative-projects).",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Print machine-readable JSON.")
def list_cmd(root_raw: Optional[str], as_json: bool) -> None:
    """List known creative projects (scans the projects root for project.md files)."""
    root = Path(root_raw) if root_raw else None
    projects = list_projects(root)

    if as_json:
        _print_json({"projects": projects})
        return

    if not projects:
        click.echo("No projects found.")
        return

    for p in projects:
        click.echo(f"{p['name']}  [{p['type']}]  status={p['status']}  tier={p['sensitivity_tier']}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
