"""Vision MCP server: new_project / excalidraw / assets_manifest / list_projects.

Same pattern as Friday, Alfred and TARS (standard `mcp` package, stdio,
plain-string returns). Launch: `python -m vision.mcp_server`.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from vision.assets import build_manifest, render_markdown
from vision.cli import _vault_root
from vision.excalidraw import write_scene
from vision.projects import list_projects as _list_projects
from vision.scaffold import PROJECT_TYPES, ProjectExistsError, scaffold_project
from vision.vault import write_project_moc

server = MCPServer(
    name="vision",
    instructions=(
        "Vision is the user's creative-project agent: scaffolds project "
        "folders, writes blank Excalidraw files, catalogs assets. It never "
        "drives external creative apps. Projects marked private route their "
        "vault note to vault/Vision/private/."
    ),
)


@server.tool(description=f"Create a creative project. project_type is one of {list(PROJECT_TYPES)}. private=true marks it private-tier.")
def new_project(name: str, project_type: str, private: bool = False) -> str:
    try:
        result = scaffold_project(name, project_type, private=private)
    except (ProjectExistsError, ValueError) as exc:
        return f"Error: {exc}"
    moc = write_project_moc(
        name, project_type, status=result["status"], private=private,
        project_path=result["path"], vault_root=_vault_root(),
    )
    return json.dumps({**{k: str(v) for k, v in result.items()}, "vault_moc": str(moc)}, indent=2)


@server.tool(description="Write a blank valid .excalidraw file. project_dir optional (writes to <project_dir>/assets/).")
def excalidraw(name: str, project_dir: str = "") -> str:
    target = Path(project_dir) / "assets" / name if project_dir.strip() else Path.cwd() / name
    return f"Created: {write_scene(target, name=name)}"


@server.tool(description="Markdown catalog of a project's assets/ and exports/ folders.")
def assets_manifest(project_dir: str) -> str:
    path = Path(project_dir)
    if not path.is_dir():
        return f"Error: not a directory: {project_dir}"
    return render_markdown(build_manifest(path), project_name=path.name)


@server.tool(description="List known creative projects (name, type, status, tier).")
def list_projects() -> str:
    return json.dumps(_list_projects(), indent=2, default=str)


@server.tool(description="Draw an Excalidraw diagram from text. 'A -> B: label, B -> C' is parsed offline; plain English is turned into boxes/arrows by the local model. project_dir optional (writes to <project_dir>/assets/).")
def diagram(description: str, name: str = "diagram", project_dir: str = "") -> str:
    from vision import diagram as d

    target = Path(project_dir) / "assets" / name if project_dir.strip() else Path.cwd() / name
    try:
        return f"Created: {d.write_diagram(target, d.graph_from_input(description))}"
    except d.DiagramError as exc:
        return f"Error: {exc}"


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
