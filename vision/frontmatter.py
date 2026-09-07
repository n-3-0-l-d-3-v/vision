"""Tiny YAML-frontmatter reader/writer shared by scaffold.py and vault.py.

Deliberately not a full YAML round-trip (PyYAML would happily do that, but
project.md and MOC notes only ever need a flat string-keyed frontmatter
block, matching the simple `key: value` frontmatter Ultron/Alfred/Wall-E's
own vault notes use) -- a hand-rolled reader/writer keeps the on-disk
format predictable and diff-friendly, and avoids round-tripping through a
generic YAML dumper that might reformat things a human editor wouldn't.
"""

from __future__ import annotations

import re

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", re.DOTALL)


def render(fields: dict, body: str = "") -> str:
    """Render `fields` as a `---`-delimited frontmatter block followed by
    `body`. Values are written as plain scalars (no quoting/escaping) --
    callers are responsible for keeping values simple (no embedded
    newlines or leading `---`), which holds for every field Vision writes
    (names, dates, enum-like status/type/tier strings)."""
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    header = "\n".join(lines)
    return header + body


def parse(text: str) -> tuple[dict, str]:
    """Parse a `render()`-produced document back into (fields, body). If
    `text` has no frontmatter block, returns ({}, text) unchanged."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    fields: dict = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, match.group(2)


__all__ = ["parse", "render"]
