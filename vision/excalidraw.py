"""Excalidraw starter-file generation (`vision excalidraw`).

`.excalidraw` files are plain JSON with a well-known scene schema -- no
Excalidraw install needed to produce a syntactically valid, openable
starter file. The shape below matches what Excalidraw's own web app
(https://excalidraw.com) writes when you use File > Save to... on a blank
canvas, and what it accepts on File > Open:

    {
      "type": "excalidraw",
      "version": 2,
      "source": "https://excalidraw.com",
      "elements": [],
      "appState": {
        "gridSize": null,
        "viewBackgroundColor": "#ffffff"
      },
      "files": {}
    }

- `type` must be the literal string `"excalidraw"` -- this is how the app
  identifies a scene file on import.
- `version` is the scene schema version; `2` is current (has been since
  Excalidraw's frontmatter-versioning scheme replaced the old numeric
  `version` counter semantics years ago -- this is the *schema* version,
  not an autosave revision counter).
- `source` records the app/URL that produced the file; Excalidraw sets it
  to its own URL and does not require it on import, but a real exported
  file always has it, so v1 includes it too.
- `elements` is the array of drawn elements (shapes, text, arrows, ...) --
  empty for a fresh starter file.
- `appState` carries UI/canvas state; only `gridSize` and
  `viewBackgroundColor` are meaningful for a blank starter (Excalidraw
  fills in everything else with its own defaults on import), matching
  what a real blank-canvas export contains.
- `files` holds embedded binary assets (e.g. pasted images) keyed by file
  id; empty for a starter file with no elements.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

SCHEMA_TYPE = "excalidraw"
SCHEMA_VERSION = 2
SCHEMA_SOURCE = "https://excalidraw.com"

REQUIRED_KEYS = ("type", "version", "elements", "appState")


def new_scene(name: Optional[str] = None) -> dict:
    """Build a blank Excalidraw scene dict. `name` is currently unused by
    the schema itself (Excalidraw derives a document's display name from
    its filename, not from scene content) but accepted for a symmetrical,
    future-proof call signature."""
    return {
        "type": SCHEMA_TYPE,
        "version": SCHEMA_VERSION,
        "source": SCHEMA_SOURCE,
        "elements": [],
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff",
        },
        "files": {},
    }


def write_scene(path: Path, name: Optional[str] = None) -> Path:
    """Write a blank Excalidraw scene to `path`. Appends `.excalidraw` if
    `path` doesn't already have that suffix, so `vision excalidraw foo`
    and `vision excalidraw foo.excalidraw` both do the right thing."""
    if path.suffix != ".excalidraw":
        path = path.with_name(path.name + ".excalidraw")
    path.parent.mkdir(parents=True, exist_ok=True)
    scene = new_scene(name or path.stem)
    path.write_text(json.dumps(scene, indent=2), encoding="utf-8")
    return path


def is_valid_scene(data: dict) -> bool:
    """Structural check: does `data` have every key a real Excalidraw
    scene needs (`type`, `version`, `elements`, `appState`), with the
    right value for `type`?"""
    if not isinstance(data, dict):
        return False
    if any(key not in data for key in REQUIRED_KEYS):
        return False
    if data.get("type") != SCHEMA_TYPE:
        return False
    if not isinstance(data.get("elements"), list):
        return False
    if not isinstance(data.get("appState"), dict):
        return False
    return True


__all__ = [
    "REQUIRED_KEYS",
    "SCHEMA_SOURCE",
    "SCHEMA_TYPE",
    "SCHEMA_VERSION",
    "is_valid_scene",
    "new_scene",
    "write_scene",
]
