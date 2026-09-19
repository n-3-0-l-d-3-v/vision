import asyncio
import json

from vision import mcp_server


def _call(name, args):
    res = asyncio.run(mcp_server.server.call_tool(name, args))
    return res


def test_tools_registered():
    tools = asyncio.run(mcp_server.server.list_tools())
    assert {t.name for t in tools} >= {"new_project", "excalidraw", "assets_manifest", "list_projects"}


def test_excalidraw_and_assets(tmp_path):
    out = str(_call("excalidraw", {"name": "d.excalidraw", "project_dir": str(tmp_path)}))
    assert "d.excalidraw" in out
    assert (tmp_path / "assets" / "d.excalidraw").exists()
    assert "d.excalidraw" in str(_call("assets_manifest", {"project_dir": str(tmp_path)}))


def test_new_project_rejects_bad_type(tmp_path, monkeypatch):
    monkeypatch.setenv("VISION_PROJECTS_ROOT", str(tmp_path))
    assert "Error" in str(_call("new_project", {"name": "x", "project_type": "nope"}))
