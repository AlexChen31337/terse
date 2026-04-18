"""
Basic validation tests for the whalecli unified skill.

Verifies that SKILL.md and skill.toml are consistent and well-formed
according to the Unified Skill Specification.

Run with:
    uv run python -m pytest skills/whalecli/tests/ -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Use bridge.py from skill-bridge for validation
BRIDGE_SCRIPTS = Path(__file__).parent.parent.parent / "skill-bridge" / "scripts"
sys.path.insert(0, str(BRIDGE_SCRIPTS))

from bridge import parse_skill_md, parse_skill_toml, validate_skill

WHALECLI_DIR = Path(__file__).parent.parent


class TestWhaleCliSkillMd:
    def test_frontmatter_present(self) -> None:
        fm, body = parse_skill_md(WHALECLI_DIR)
        assert fm.name == "whalecli"
        assert fm.version == "1.0.0"
        assert fm.description
        assert fm.author

    def test_evoclaw_metadata(self) -> None:
        fm, _ = parse_skill_md(WHALECLI_DIR)
        assert "network" in fm.permissions
        assert "ETHERSCAN_API_KEY" in fm.env

    def test_tags_present(self) -> None:
        fm, _ = parse_skill_md(WHALECLI_DIR)
        assert "crypto" in fm.tags or len(fm.tags) > 0

    def test_body_has_sections(self) -> None:
        _, body = parse_skill_md(WHALECLI_DIR)
        assert "## When to Use" in body
        assert "## Quick Start" in body or "## Install" in body


class TestWhaleCliSkillToml:
    def test_basic_fields(self) -> None:
        st = parse_skill_toml(WHALECLI_DIR)
        assert st.name == "whalecli"
        assert st.version == "1.0.0"
        assert st.openclaw is True
        assert st.evoclaw is True

    def test_tools_defined(self) -> None:
        st = parse_skill_toml(WHALECLI_DIR)
        assert "scan" in st.tools
        assert "check" in st.tools
        assert "stream" in st.tools

    def test_tool_commands_use_uv(self) -> None:
        st = parse_skill_toml(WHALECLI_DIR)
        for name, tool in st.tools.items():
            assert tool.command.startswith("uv run python"), (
                f"Tool '{name}' command should start with 'uv run python', got: {tool.command!r}"
            )

    def test_genome_params_in_bounds(self) -> None:
        st = parse_skill_toml(WHALECLI_DIR)
        for pk, gp in st.genome_params.items():
            if gp.min is not None and gp.max is not None and gp.value is not None:
                try:
                    v, lo, hi = float(gp.value), float(gp.min), float(gp.max)
                    assert lo <= v <= hi, (
                        f"Genome param '{pk}': value={gp.value} not in [{gp.min}, {gp.max}]"
                    )
                except (TypeError, ValueError):
                    pass  # bool params skip numeric check

    def test_evoclaw_metadata_matches_skill_md(self) -> None:
        fm, _ = parse_skill_md(WHALECLI_DIR)
        st = parse_skill_toml(WHALECLI_DIR)
        assert fm.name == st.name, f"Name mismatch: SKILL.md={fm.name!r}, skill.toml={st.name!r}"
        assert fm.version == st.version, f"Version mismatch: SKILL.md={fm.version!r}, skill.toml={st.version!r}"


class TestWhaleCliUnifiedValidation:
    def test_passes_bridge_validation(self) -> None:
        vr = validate_skill(WHALECLI_DIR)
        # Report for debug info
        if not vr.ok:
            print("Errors:", vr.errors)
            print("Warnings:", vr.warnings)
        assert vr.ok, f"Bridge validation failed: {vr.errors}"
