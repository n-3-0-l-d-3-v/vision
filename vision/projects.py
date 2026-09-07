"""Project discovery (`vision list`): scan the projects root for
`project.md` files and summarize what's there.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from vision.scaffold import PROJECT_FILENAME, default_projects_root, read_project_md


def list_projects(root: Optional[Path] = None) -> list[dict]:
    """Scan `root` (or `default_projects_root()`) one level deep for
    `<project-dir>/project.md` files and return a list of summaries:
    `name` (directory name), `path`, plus whatever frontmatter fields
    `project.md` has (`title`, `type`, `status`, `sensitivity_tier`,
    `created`). A directory without a readable `project.md` is silently
    skipped -- `vision list` reports Vision-scaffolded projects, not every
    stray folder under the root."""
    base = root if root is not None else default_projects_root()
    if not base.is_dir():
        return []

    results: list[dict] = []
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        project_md = entry / PROJECT_FILENAME
        if not project_md.is_file():
            continue
        fields = read_project_md(project_md)
        if not fields:
            continue
        results.append(
            {
                "name": entry.name,
                "path": entry,
                "title": fields.get("title", entry.name),
                "type": fields.get("type"),
                "status": fields.get("status"),
                "sensitivity_tier": fields.get("sensitivity_tier"),
                "created": fields.get("created"),
            }
        )
    return results


__all__ = ["list_projects"]
