"""Vault MOC (map-of-content) integration: every `vision new` writes a
project note to `vault/Vision/`, matching the pattern Ultron/Alfred/Wall-E
already use for their own vault folders -- this repo owns a local
`vault/Vision/` path, and a future ecosystem bootstrap step is expected to
symlink or mount that path at wherever the real shared vault lives; this
module does not know or care where that is.

Sensitivity-tier routing: a `--private` project's MOC note is written to
`vault/Vision/private/` instead of `vault/Vision/`, matching the
ecosystem-wide `vault/private/` vs `vault/public/` convention documented
in `10x/docs/omniroute-privacy-spec.md`, scoped down to Vision's own vault
subtree (Vision doesn't own the top-level `vault/private/` split, just its
own corner of it). This is a real routing decision the tests exercise --
not a flag that's accepted and ignored.
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Optional

from vision.frontmatter import render

#: Default local vault root, matching agent.yaml's vault_write_path.
VAULT_ROOT_DEFAULT = Path("vault") / "Vision"
PRIVATE_SUBDIR = "private"


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "project"


def moc_path(name: str, *, private: bool, vault_root: Optional[Path] = None) -> Path:
    """Where a project's MOC note lives: `<vault_root>/<slug>.md`, or
    `<vault_root>/private/<slug>.md` for a `--private` project."""
    root = vault_root if vault_root is not None else VAULT_ROOT_DEFAULT
    if private:
        root = root / PRIVATE_SUBDIR
    return root / f"{_slugify(name)}.md"


def write_project_moc(
    name: str,
    project_type: str,
    *,
    status: str = "active",
    private: bool = False,
    project_path: Optional[Path] = None,
    vault_root: Optional[Path] = None,
) -> Path:
    """Write (or overwrite) a project's MOC note. Returns the path
    written. Routes to `vault/Vision/private/` when `private=True`, per
    the module docstring -- this is the one place that routing decision
    is made, so `vision new --private` and any future caller share it."""
    path = moc_path(name, private=private, vault_root=vault_root)
    path.parent.mkdir(parents=True, exist_ok=True)

    created = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tier = "private" if private else "work"
    fields = {
        "title": name,
        "type": project_type,
        "status": status,
        "sensitivity_tier": tier,
        "created": created,
        "agent": "Vision",
    }
    body_lines = [
        "",
        f"# {name} (MOC)",
        "",
        f"Creative project of type **{project_type}**, sensitivity tier `{tier}`.",
        "",
    ]
    if project_path is not None:
        body_lines.append(f"Project folder: `{project_path}`")
        body_lines.append("")
    body_lines.extend(
        [
            "## Notes",
            "",
            "## Decisions",
            "",
        ]
    )
    body = "\n".join(body_lines) + "\n"

    path.write_text(render(fields, body), encoding="utf-8")
    return path


def append_note(path: Path, heading: str, text: str) -> None:
    """Append a timestamped line under `heading`'s section in an existing
    MOC note. If `heading` isn't found, the text is appended at the end of
    the file under a freshly-created `heading` section. Used for the
    "running list of the project's own notes/decisions" the task spec
    calls for; not wired to a CLI command in v1 (no command yet needs it),
    but exercised directly by tests since it is real, working behavior."""
    if not path.exists():
        raise FileNotFoundError(f"no MOC note at {path}")

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry = f"- [{timestamp}] {text}"

    content = path.read_text(encoding="utf-8")
    heading_line = f"## {heading}"
    lines = content.splitlines()

    if heading_line in lines:
        idx = lines.index(heading_line)
        insert_at = idx + 1
        # Skip a single blank line right after the heading, if present.
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        lines.insert(insert_at, entry)
    else:
        if lines and lines[-1].strip() != "":
            lines.append("")
        lines.append(heading_line)
        lines.append("")
        lines.append(entry)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


__all__ = [
    "PRIVATE_SUBDIR",
    "VAULT_ROOT_DEFAULT",
    "append_note",
    "moc_path",
    "write_project_moc",
]
