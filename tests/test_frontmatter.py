from __future__ import annotations

from vision.frontmatter import parse, render


def test_render_then_parse_roundtrips_fields():
    fields = {"title": "Demo", "type": "music", "status": "active"}
    text = render(fields, "\n# Demo\n\nbody text\n")

    parsed_fields, body = parse(text)
    assert parsed_fields == fields
    assert "# Demo" in body
    assert "body text" in body


def test_parse_no_frontmatter_returns_empty_fields():
    fields, body = parse("just plain text, no frontmatter")
    assert fields == {}
    assert body == "just plain text, no frontmatter"


def test_render_frontmatter_block_is_dash_delimited():
    text = render({"a": "1"}, "body")
    lines = text.splitlines()
    assert lines[0] == "---"
    assert "a: 1" in lines
    assert lines.count("---") == 2
