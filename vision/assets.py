"""Asset manifest / cataloging (`vision assets`).

Walks a creative project's `assets/` and `exports/` folders and produces a
manifest of what's there: name, size, type (by extension), last-modified.
Pure filesystem work -- no creative-app dependency, matching the "what do
I have in this project" job the task spec calls for without needing to
open anything.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Optional

#: Subfolders scanned for a manifest, matching scaffold.SUBFOLDERS minus
#: `drafts/` -- drafts are in-progress work-in-progress files, not
#: finished/organized assets, so a manifest of "what do I have" is scoped
#: to `assets/` (source material) and `exports/` (finished output) per the
#: task spec's explicit wording ("Walks a creative project's assets/+
#: exports/ folders").
MANIFEST_SCAN_DIRS = ("assets", "exports")


def _file_type(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return ext or "unknown"


def build_manifest(project_dir: Path) -> list[dict]:
    """Walk `project_dir`'s `assets/` and `exports/` subfolders
    (recursively) and return a list of entries: `name`, `relative_path`,
    `folder` (which top-level scan dir it's under), `size_bytes`, `type`,
    `modified` (ISO 8601, local file mtime). Missing scan dirs are simply
    skipped -- a fresh `vision new` project has empty `assets/`/`exports/`
    dirs, which is a valid, unremarkable state, not an error."""
    project_dir = Path(project_dir)
    entries: list[dict] = []

    for scan_dir_name in MANIFEST_SCAN_DIRS:
        scan_dir = project_dir / scan_dir_name
        if not scan_dir.is_dir():
            continue
        for path in sorted(scan_dir.rglob("*")):
            if not path.is_file():
                continue
            stat = path.stat()
            modified = datetime.datetime.fromtimestamp(
                stat.st_mtime, tz=datetime.timezone.utc
            ).isoformat()
            entries.append(
                {
                    "name": path.name,
                    "relative_path": str(path.relative_to(project_dir)).replace("\\", "/"),
                    "folder": scan_dir_name,
                    "size_bytes": stat.st_size,
                    "type": _file_type(path),
                    "modified": modified,
                }
            )

    return entries


def render_markdown(entries: list[dict], project_name: Optional[str] = None) -> str:
    """Render a manifest as a Markdown table."""
    lines: list[str] = []
    title = f"Asset Manifest — {project_name}" if project_name else "Asset Manifest"
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"{len(entries)} file(s) found under `assets/` and `exports/`.")
    lines.append("")
    if entries:
        lines.append("| Name | Folder | Type | Size (bytes) | Modified |")
        lines.append("|---|---|---|---|---|")
        for e in entries:
            lines.append(
                f"| {e['name']} | {e['folder']} | {e['type']} | "
                f"{e['size_bytes']} | {e['modified']} |"
            )
    else:
        lines.append("_No files found._")
    lines.append("")
    return "\n".join(lines)


def write_manifest(
    project_dir: Path,
    *,
    fmt: str = "json",
    filename: Optional[str] = None,
) -> Path:
    """Build the manifest and write it to `project_dir` as JSON or
    Markdown. Returns the path written."""
    if fmt not in ("json", "md"):
        raise ValueError(f"unknown manifest format {fmt!r}; must be 'json' or 'md'")

    project_dir = Path(project_dir)
    entries = build_manifest(project_dir)

    if filename is None:
        filename = "vision-assets-manifest.json" if fmt == "json" else "vision-assets-manifest.md"
    out_path = project_dir / filename

    if fmt == "json":
        out_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    else:
        out_path.write_text(render_markdown(entries, project_name=project_dir.name), encoding="utf-8")

    return out_path


__all__ = [
    "MANIFEST_SCAN_DIRS",
    "build_manifest",
    "render_markdown",
    "write_manifest",
]
