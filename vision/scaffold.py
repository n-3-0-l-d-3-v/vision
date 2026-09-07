"""Creative project scaffolding (`vision new`).

Creates a standard folder structure (`assets/`, `exports/`, `drafts/`) plus
a `project.md` map-of-content-style file with YAML frontmatter recording
type/created-date/status/sensitivity tier, under a configurable projects
root. This is genuinely useful organizational scaffolding regardless of
which actual creative app the user later opens to do the work in -- it
does not shell out to or assume the presence of any DAW/design/video tool
(see 10x/docs/phases/README.md Phase 3, explicitly deferred on this
machine).
"""

from __future__ import annotations

import datetime
import os
import re
from pathlib import Path
from typing import Optional

from vision.frontmatter import parse, render

#: The six creative-work categories Vision v1 scaffolds for, per the task
#: spec. Kept as an explicit tuple (not "any string") so `vision new
#: --type bogus` fails loudly instead of silently creating a category that
#: nothing else in the ecosystem recognizes.
PROJECT_TYPES = ("music", "design", "video", "photo", "writing", "game")

#: Subfolders created under every project, regardless of type. The task
#: spec calls out `assets/`, `exports/`, `drafts/` as "a standard project
#: folder structure" -- v1 keeps this identical across types rather than
#: inventing type-specific layouts (e.g. DAW session folders), since that
#: would start assuming a specific creative app's project conventions,
#: which is exactly what's deferred for v1 (see agent.yaml / README.md).
SUBFOLDERS = ("assets", "exports", "drafts")

PROJECT_FILENAME = "project.md"

ENV_ROOT_VAR = "VISION_PROJECTS_ROOT"


class ProjectExistsError(Exception):
    """Raised by scaffold_project when the target project directory already exists."""


def default_projects_root() -> Path:
    """The default projects root: `VISION_PROJECTS_ROOT` env var if set,
    else `~/Desktop/Neil/creative-projects` (this machine's actual home
    layout, matching the task spec's example default)."""
    override = os.environ.get(ENV_ROOT_VAR)
    if override:
        return Path(override)
    return Path.home() / "Desktop" / "Neil" / "creative-projects"


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip()).strip("-")
    return slug or "project"


def project_dir(name: str, root: Optional[Path] = None) -> Path:
    """The directory a project named `name` would live in under `root`
    (or `default_projects_root()`). Uses the raw name as the directory
    name -- slugified only as a fallback if the name is nothing but
    non-filesystem-safe characters (see `_slugify`)."""
    base = root if root is not None else default_projects_root()
    safe_name = name.strip()
    if not safe_name or any(ch in safe_name for ch in '<>:"/\\|?*'):
        safe_name = _slugify(name)
    return base / safe_name


def scaffold_project(
    name: str,
    project_type: str,
    *,
    private: bool = False,
    root: Optional[Path] = None,
) -> dict:
    """Create a new creative project: folder structure + `project.md`.

    Returns a dict describing what was created: `name`, `type`, `status`,
    `sensitivity_tier`, `path`, `project_md_path`, `created`.

    Raises `ValueError` for an unrecognized `project_type`, and
    `ProjectExistsError` if the target directory already exists (v1 never
    silently overwrites an existing project).
    """
    if project_type not in PROJECT_TYPES:
        raise ValueError(
            f"unknown project type {project_type!r}; must be one of {PROJECT_TYPES}"
        )
    if not name.strip():
        raise ValueError("project name must not be empty")

    target = project_dir(name, root=root)
    if target.exists():
        raise ProjectExistsError(f"project directory already exists: {target}")

    for sub in SUBFOLDERS:
        (target / sub).mkdir(parents=True, exist_ok=True)

    created = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tier = "private" if private else "work"
    status = "active"

    fields = {
        "title": name,
        "type": project_type,
        "created": created,
        "status": status,
        "sensitivity_tier": tier,
    }
    body = (
        f"\n# {name}\n\n"
        f"## Overview\n\n"
        f"_What is this project? Fill in._\n\n"
        f"## Notes\n\n"
        f"## Decisions\n\n"
        f"## Assets\n\n"
        f"See `assets/` and `exports/`, or run `vision assets .` from this "
        f"directory for a generated manifest.\n"
    )
    project_md_path = target / PROJECT_FILENAME
    project_md_path.write_text(render(fields, body), encoding="utf-8")

    return {
        "name": name,
        "type": project_type,
        "status": status,
        "sensitivity_tier": tier,
        "path": target,
        "project_md_path": project_md_path,
        "created": created,
    }


def read_project_md(path: Path) -> dict:
    """Parse a `project.md` file's frontmatter. Returns {} if the file
    doesn't exist or has no frontmatter block."""
    if not path.exists():
        return {}
    fields, _ = parse(path.read_text(encoding="utf-8"))
    return fields


__all__ = [
    "ENV_ROOT_VAR",
    "PROJECT_FILENAME",
    "PROJECT_TYPES",
    "SUBFOLDERS",
    "ProjectExistsError",
    "default_projects_root",
    "project_dir",
    "read_project_md",
    "scaffold_project",
]
