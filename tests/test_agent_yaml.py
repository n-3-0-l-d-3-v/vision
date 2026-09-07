from __future__ import annotations

from pathlib import Path

import yaml

REQUIRED_FIELDS = (
    "name",
    "role",
    "default_sensitivity_tier",
    "entrypoint",
    "health_check_command",
    "sandboxed",
)
VALID_TIERS = {"private", "personal-token", "work", "public"}

AGENT_YAML_PATH = Path(__file__).resolve().parents[1] / "agent.yaml"


def _load():
    text = AGENT_YAML_PATH.read_text(encoding="utf-8")
    return yaml.safe_load(text)


def test_agent_yaml_parses_as_mapping():
    data = _load()
    assert isinstance(data, dict)


def test_agent_yaml_has_all_required_fields():
    data = _load()
    missing = [f for f in REQUIRED_FIELDS if f not in data or data[f] is None]
    assert missing == []


def test_agent_yaml_tier_is_valid():
    data = _load()
    assert data["default_sensitivity_tier"] in VALID_TIERS


def test_agent_yaml_matches_ecosystem_contract():
    data = _load()
    assert data["name"] == "Vision"
    assert data["entrypoint"] == "vision"
    assert data["health_check_command"] == "vision --health"
    assert data["default_sensitivity_tier"] == "work"
    assert data["sandboxed"] is False
    assert data["vault_write_path"] == "vault/Vision/"
