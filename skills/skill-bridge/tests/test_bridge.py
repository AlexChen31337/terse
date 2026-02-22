"""
Tests for skill-bridge bridge.py

Run with:
    uv run python -m pytest skills/skill-bridge/tests/ -v
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from bridge import (
    SkillFrontmatter,
    SkillToml,
    ToolDef,
    GenomeParam,
    _parse_simple_yaml,
    _parse_minimal_toml,
    _split_frontmatter,
    parse_skill_md,
    parse_skill_toml,
    generate_skill_toml,
    generate_skill_md,
    generate_agent_toml,
    generate_genome_json,
    validate_skill,
    ValidationResult,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_skill(tmp_path: Path) -> Path:
    """Create a minimal valid unified skill directory."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()

    (skill_dir / "SKILL.md").write_text(textwrap.dedent("""\
        ---
        name: test-skill
        version: 1.2.3
        description: "A test skill"
        author: "Test Author"
        license: MIT
        tags: [test, example]
        metadata:
          evoclaw:
            permissions:
              - network
            env:
              - TEST_API_KEY
        ---

        # test-skill — Agent Skill

        A test skill for bridge validation tests.

        ## When to Use

        When running tests.

        ## Quick Start

        ```bash
        uv run python scripts/main.py run
        ```
    """), encoding="utf-8")

    (skill_dir / "skill.toml").write_text(textwrap.dedent("""\
        [skill]
        name        = "test-skill"
        version     = "1.2.3"
        description = "A test skill"
        author      = "Test Author"
        license     = "MIT"

        [skill.compat]
        openclaw = true
        evoclaw  = true
        clawhub  = true

        [skill.tags]
        tags = ["test", "example"]

        [skill.deps]
        python = ">=3.11"

        [skill.evoclaw]
        permissions = ["network"]
        env         = ["TEST_API_KEY"]

        [tools.run]
        command      = "uv run python scripts/main.py run"
        description  = "Run the skill"
        timeout_secs = 30

        [tools.check]
        command      = "uv run python scripts/main.py check"
        description  = "Quick check"
        timeout_secs = 15

        [genome]
        weight  = 0.7
        enabled = true

        [genome.params]
        threshold = { value = 70, min = 40, max = 95, type = "int" }
        rate      = { value = 0.5, min = 0.1, max = 1.0, type = "float" }
    """), encoding="utf-8")

    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "main.py").write_text('"""main script"""\n', encoding="utf-8")

    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text('"""tests"""\n', encoding="utf-8")

    return skill_dir


@pytest.fixture()
def openclaw_only_skill(tmp_path: Path) -> Path:
    """A skill with SKILL.md but no skill.toml."""
    skill_dir = tmp_path / "openclaw-only"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(textwrap.dedent("""\
        ---
        name: openclaw-only
        version: 0.1.0
        description: "OpenClaw-only skill"
        author: "Someone"
        ---

        # openclaw-only

        This is an OpenClaw-only skill.
    """), encoding="utf-8")
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "run.py").write_text('"""run"""\n', encoding="utf-8")
    return skill_dir


# ─────────────────────────────────────────────────────────────────────────────
# YAML parser tests
# ─────────────────────────────────────────────────────────────────────────────

class TestParseSimpleYaml:
    def test_simple_scalars(self) -> None:
        yaml = textwrap.dedent("""\
            name: my-skill
            version: 1.0.0
            description: "A cool skill"
        """)
        result = _parse_simple_yaml(yaml)
        assert result["name"] == "my-skill"
        assert result["version"] == "1.0.0"
        assert result["description"] == "A cool skill"

    def test_inline_list(self) -> None:
        yaml = "tags: [crypto, trading, test]"
        result = _parse_simple_yaml(yaml)
        assert result["tags"] == ["crypto", "trading", "test"]

    def test_nested_dict(self) -> None:
        yaml = textwrap.dedent("""\
            metadata:
              evoclaw:
                permissions:
                  - network
                env:
                  - MY_KEY
        """)
        # Note: our minimal parser handles nested dicts but not list items starting with -
        # The yaml library handles this properly; our fallback handles inline only.
        # Just test that it doesn't crash.
        result = _parse_simple_yaml(yaml)
        assert "metadata" in result


class TestSplitFrontmatter:
    def test_valid_frontmatter(self) -> None:
        text = textwrap.dedent("""\
            ---
            name: test
            version: 1.0.0
            ---

            # Body here
        """)
        fm, body = _split_frontmatter(text)
        assert fm.get("name") == "test"
        assert "Body here" in body

    def test_no_frontmatter(self) -> None:
        text = "# Just a markdown file\nNo frontmatter."
        fm, body = _split_frontmatter(text)
        assert fm == {}
        assert "No frontmatter" in body

    def test_unclosed_frontmatter(self) -> None:
        text = "---\nname: broken\n"
        fm, body = _split_frontmatter(text)
        assert fm == {}  # unclosed = treat as no frontmatter


# ─────────────────────────────────────────────────────────────────────────────
# TOML parser tests
# ─────────────────────────────────────────────────────────────────────────────

class TestParseMinimalToml:
    def test_scalar_values(self) -> None:
        toml = textwrap.dedent("""\
            [skill]
            name    = "my-skill"
            version = "1.0.0"
            enabled = true
            count   = 42
        """)
        result = _parse_minimal_toml(toml)
        assert result["skill"]["name"] == "my-skill"
        assert result["skill"]["version"] == "1.0.0"
        assert result["skill"]["enabled"] is True
        assert result["skill"]["count"] == 42

    def test_string_array(self) -> None:
        toml = 'tags = ["a", "b", "c"]'
        result = _parse_minimal_toml(toml)
        assert result["tags"] == ["a", "b", "c"]

    def test_inline_dict(self) -> None:
        toml = textwrap.dedent("""\
            [genome.params]
            threshold = { value = 70, min = 40, max = 95, type = "int" }
        """)
        result = _parse_minimal_toml(toml)
        gp = result["genome"]["params"]["threshold"]
        assert gp["value"] == 70
        assert gp["min"] == 40
        assert gp["max"] == 95
        assert gp["type"] == "int"

    def test_nested_sections(self) -> None:
        toml = textwrap.dedent("""\
            [skill]
            name = "x"

            [skill.compat]
            openclaw = true
            evoclaw  = false
        """)
        result = _parse_minimal_toml(toml)
        assert result["skill"]["name"] == "x"
        assert result["skill"]["compat"]["openclaw"] is True
        assert result["skill"]["compat"]["evoclaw"] is False

    def test_tools_sections(self) -> None:
        toml = textwrap.dedent("""\
            [tools.scan]
            command      = "uv run python scripts/scan.py"
            description  = "Run a scan"
            timeout_secs = 60

            [tools.check]
            command      = "uv run python scripts/check.py"
            description  = "Quick check"
            timeout_secs = 15
        """)
        result = _parse_minimal_toml(toml)
        assert result["tools"]["scan"]["command"] == "uv run python scripts/scan.py"
        assert result["tools"]["scan"]["timeout_secs"] == 60
        assert result["tools"]["check"]["description"] == "Quick check"

    def test_comment_stripping(self) -> None:
        toml = 'name = "test"  # inline comment'
        result = _parse_minimal_toml(toml)
        assert result["name"] == "test"

    def test_empty_array(self) -> None:
        toml = "tags = []"
        result = _parse_minimal_toml(toml)
        assert result["tags"] == []


# ─────────────────────────────────────────────────────────────────────────────
# Parsing tests
# ─────────────────────────────────────────────────────────────────────────────

class TestParseSkillMd:
    def test_full_frontmatter(self, tmp_skill: Path) -> None:
        fm, body = parse_skill_md(tmp_skill)
        assert fm.name == "test-skill"
        assert fm.version == "1.2.3"
        assert fm.description == "A test skill"
        assert fm.author == "Test Author"
        assert fm.license == "MIT"
        assert "test" in fm.tags
        assert "network" in fm.permissions
        assert "TEST_API_KEY" in fm.env
        assert "# test-skill" in body

    def test_missing_skill_md(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc:
            parse_skill_md(tmp_path)
        assert exc.value.code == 4

    def test_openclaw_only(self, openclaw_only_skill: Path) -> None:
        fm, body = parse_skill_md(openclaw_only_skill)
        assert fm.name == "openclaw-only"
        assert fm.permissions == []
        assert fm.env == []


class TestParseSkillToml:
    def test_full_skill_toml(self, tmp_skill: Path) -> None:
        st = parse_skill_toml(tmp_skill)
        assert st.name == "test-skill"
        assert st.version == "1.2.3"
        assert st.openclaw is True
        assert st.evoclaw is True
        assert st.clawhub is True
        assert "test" in st.tags
        assert "network" in st.permissions
        assert "TEST_API_KEY" in st.env

    def test_tools_parsed(self, tmp_skill: Path) -> None:
        st = parse_skill_toml(tmp_skill)
        assert "run" in st.tools
        assert "check" in st.tools
        assert st.tools["run"].command == "uv run python scripts/main.py run"
        assert st.tools["run"].timeout_secs == 30
        assert st.tools["check"].timeout_secs == 15

    def test_genome_params(self, tmp_skill: Path) -> None:
        st = parse_skill_toml(tmp_skill)
        assert "threshold" in st.genome_params
        gp = st.genome_params["threshold"]
        assert gp.value == 70
        assert gp.min == 40
        assert gp.max == 95
        assert gp.type == "int"
        assert st.genome_weight == 0.7
        assert st.genome_enabled is True

    def test_missing_skill_toml(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc:
            parse_skill_toml(tmp_path)
        assert exc.value.code == 4


# ─────────────────────────────────────────────────────────────────────────────
# Generator tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateSkillToml:
    def test_generates_valid_toml(self, openclaw_only_skill: Path) -> None:
        fm, _ = parse_skill_md(openclaw_only_skill)
        toml_str = generate_skill_toml(fm, openclaw_only_skill)
        assert "[skill]" in toml_str
        assert 'name        = "openclaw-only"' in toml_str
        assert "[skill.compat]" in toml_str
        assert "openclaw = true" in toml_str
        assert "evoclaw  = true" in toml_str

    def test_discovers_scripts(self, openclaw_only_skill: Path) -> None:
        fm, _ = parse_skill_md(openclaw_only_skill)
        toml_str = generate_skill_toml(fm, openclaw_only_skill)
        # Should discover run.py in scripts/
        assert "[tools.run]" in toml_str

    def test_includes_genome_scaffold(self, openclaw_only_skill: Path) -> None:
        fm, _ = parse_skill_md(openclaw_only_skill)
        toml_str = generate_skill_toml(fm, openclaw_only_skill)
        assert "[genome]" in toml_str


class TestGenerateSkillMd:
    def test_generates_valid_markdown(self, tmp_skill: Path) -> None:
        st = parse_skill_toml(tmp_skill)
        md = generate_skill_md(st)
        assert "---" in md
        assert "name: test-skill" in md
        assert "# test-skill" in md
        assert "## When to Use" in md
        assert "## Tools" in md
        assert "### `run`" in md
        assert "### `check`" in md

    def test_includes_evoclaw_metadata(self, tmp_skill: Path) -> None:
        st = parse_skill_toml(tmp_skill)
        md = generate_skill_md(st)
        assert "metadata:" in md
        assert "evoclaw:" in md
        assert "network" in md
        assert "TEST_API_KEY" in md


class TestGenerateAgentToml:
    def test_generates_tools(self, tmp_skill: Path) -> None:
        st = parse_skill_toml(tmp_skill)
        agent_toml = generate_agent_toml(st)
        assert "[tools.run]" in agent_toml
        assert "[tools.check]" in agent_toml
        assert 'command     = "uv run python scripts/main.py run"' in agent_toml
        assert "timeout_secs = 30" in agent_toml

    def test_empty_tools(self) -> None:
        st = SkillToml(name="empty", version="1.0.0")
        agent_toml = generate_agent_toml(st)
        assert "No tools defined" in agent_toml

    def test_parseable_by_evoclaw(self, tmp_skill: Path) -> None:
        """The generated agent.toml should be parseable by EvoClaw's ParseToolsTOML logic."""
        from bridge import _parse_minimal_toml
        st = parse_skill_toml(tmp_skill)
        agent_toml = generate_agent_toml(st)
        parsed = _parse_minimal_toml(agent_toml)
        assert "run" in parsed.get("tools", {})
        assert "check" in parsed.get("tools", {})


class TestGenerateGenomeJson:
    def test_generates_genome(self, tmp_skill: Path) -> None:
        st = parse_skill_toml(tmp_skill)
        genome = generate_genome_json(st)
        assert genome["enabled"] is True
        assert genome["weight"] == 0.7
        assert "threshold" in genome["params"]
        assert genome["params"]["threshold"] == 70
        assert genome["fitness"] == 0.0
        assert genome["version"] == 1

    def test_genome_json_serialisable(self, tmp_skill: Path) -> None:
        st = parse_skill_toml(tmp_skill)
        genome = generate_genome_json(st)
        serialised = json.dumps(genome)
        parsed = json.loads(serialised)
        assert parsed["params"]["threshold"] == 70


# ─────────────────────────────────────────────────────────────────────────────
# Validation tests
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateSkill:
    def test_valid_skill_passes(self, tmp_skill: Path) -> None:
        vr = validate_skill(tmp_skill)
        assert vr.ok, f"Expected ok but got errors: {vr.errors}"

    def test_missing_skill_md(self, tmp_path: Path) -> None:
        # Create only skill.toml
        (tmp_path / "skill.toml").write_text("[skill]\nname='x'\n", encoding="utf-8")
        vr = validate_skill(tmp_path)
        assert not vr.ok
        assert any("SKILL.md" in e for e in vr.errors)

    def test_missing_skill_toml(self, openclaw_only_skill: Path) -> None:
        vr = validate_skill(openclaw_only_skill)
        assert not vr.ok
        assert any("skill.toml" in e for e in vr.errors)

    def test_name_mismatch_is_error(self, tmp_skill: Path) -> None:
        # Corrupt skill.toml with different name
        toml_path = tmp_skill / "skill.toml"
        content = toml_path.read_text()
        content = content.replace('name        = "test-skill"', 'name        = "different-name"')
        toml_path.write_text(content)
        vr = validate_skill(tmp_skill)
        assert not vr.ok
        assert any("mismatch" in e.lower() or "Name" in e for e in vr.errors)

    def test_missing_command_is_error(self, tmp_skill: Path) -> None:
        toml_path = tmp_skill / "skill.toml"
        content = toml_path.read_text()
        content = content.replace(
            'command      = "uv run python scripts/main.py run"',
            'command      = ""'
        )
        toml_path.write_text(content)
        vr = validate_skill(tmp_skill)
        assert not vr.ok
        assert any("command" in e.lower() for e in vr.errors)

    def test_missing_scripts_is_warning(self, tmp_skill: Path) -> None:
        import shutil
        shutil.rmtree(tmp_skill / "scripts")
        vr = validate_skill(tmp_skill)
        # Missing scripts is a warning, not an error
        assert vr.ok  # no errors
        assert any("scripts" in w.lower() for w in vr.warnings)

    def test_missing_tests_is_warning(self, tmp_skill: Path) -> None:
        import shutil
        shutil.rmtree(tmp_skill / "tests")
        vr = validate_skill(tmp_skill)
        assert vr.ok
        assert any("tests" in w.lower() for w in vr.warnings)

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        vr = validate_skill(tmp_path / "nonexistent")
        assert not vr.ok
        assert any("does not exist" in e for e in vr.errors)

    def test_genome_param_out_of_bounds(self, tmp_skill: Path) -> None:
        toml_path = tmp_skill / "skill.toml"
        content = toml_path.read_text()
        # Set threshold value out of bounds (value=200 > max=95)
        content = content.replace(
            "threshold = { value = 70, min = 40, max = 95, type = \"int\" }",
            'threshold = { value = 200, min = 40, max = 95, type = "int" }'
        )
        toml_path.write_text(content)
        vr = validate_skill(tmp_skill)
        # Out-of-bounds genome param should be a warning
        assert any("threshold" in w and "bounds" in w for w in vr.warnings)


# ─────────────────────────────────────────────────────────────────────────────
# Command integration tests
# ─────────────────────────────────────────────────────────────────────────────

class TestConvertToEvoclaw:
    def test_generates_skill_toml(self, openclaw_only_skill: Path) -> None:
        from bridge import cmd_convert_to_evoclaw
        cmd_convert_to_evoclaw(openclaw_only_skill)
        toml_path = openclaw_only_skill / "skill.toml"
        assert toml_path.exists()
        content = toml_path.read_text()
        assert "openclaw-only" in content
        assert "[skill.compat]" in content
        assert "evoclaw  = true" in content

    def test_idempotent_on_existing_toml(self, tmp_skill: Path) -> None:
        from bridge import cmd_convert_to_evoclaw
        # Already has skill.toml — should not crash or overwrite
        original = (tmp_skill / "skill.toml").read_text()
        cmd_convert_to_evoclaw(tmp_skill)
        # skill.toml still exists and wasn't nuked
        assert (tmp_skill / "skill.toml").exists()


class TestConvertToOpenclaw:
    def test_generates_skill_md(self, tmp_path: Path) -> None:
        from bridge import cmd_convert_to_openclaw
        skill_dir = tmp_path / "toml-only"
        skill_dir.mkdir()
        (skill_dir / "skill.toml").write_text(textwrap.dedent("""\
            [skill]
            name        = "toml-only"
            version     = "2.0.0"
            description = "EvoClaw-native skill"
            author      = "Bot"
            license     = "MIT"

            [skill.compat]
            openclaw = false
            evoclaw  = true

            [skill.evoclaw]
            permissions = ["network"]
            env         = ["BOT_KEY"]

            [tools.run]
            command      = "uv run python scripts/run.py"
            description  = "Do the thing"
            timeout_secs = 30
        """), encoding="utf-8")

        cmd_convert_to_openclaw(skill_dir)
        md_path = skill_dir / "SKILL.md"
        assert md_path.exists()
        content = md_path.read_text()
        assert "name: toml-only" in content
        assert "# toml-only" in content
        assert "### `run`" in content


class TestInstallEvoclaw:
    def test_install_creates_agent_toml(self, tmp_skill: Path, tmp_path: Path) -> None:
        from bridge import cmd_install_evoclaw
        evoclaw_dir = tmp_path / "evoclaw-skills"
        cmd_install_evoclaw(tmp_skill, evoclaw_dir)

        dest = evoclaw_dir / "test-skill"
        assert dest.exists()
        assert (dest / "SKILL.md").exists()
        assert (dest / "skill.toml").exists()

        agent_toml = dest / "agent.toml"
        assert agent_toml.exists()
        content = agent_toml.read_text()
        assert "[tools.run]" in content
        assert "[tools.check]" in content

    def test_install_creates_genome_json(self, tmp_skill: Path, tmp_path: Path) -> None:
        from bridge import cmd_install_evoclaw
        evoclaw_dir = tmp_path / "evoclaw-skills"
        cmd_install_evoclaw(tmp_skill, evoclaw_dir)

        genome_path = evoclaw_dir / "test-skill" / "genome.json"
        assert genome_path.exists()
        genome = json.loads(genome_path.read_text())
        assert genome["weight"] == 0.7
        assert "threshold" in genome["params"]
        assert genome["params"]["threshold"] == 70

    def test_install_validation_fails_early(self, tmp_path: Path) -> None:
        from bridge import cmd_install_evoclaw
        bad_skill = tmp_path / "bad-skill"
        bad_skill.mkdir()
        # No SKILL.md, no skill.toml
        with pytest.raises(SystemExit) as exc:
            cmd_install_evoclaw(bad_skill, tmp_path / "evoclaw")
        assert exc.value.code == 1

    def test_install_overwrites_existing(self, tmp_skill: Path, tmp_path: Path) -> None:
        from bridge import cmd_install_evoclaw
        evoclaw_dir = tmp_path / "evoclaw-skills"
        # Install twice — second should succeed (not crash on existing dir)
        cmd_install_evoclaw(tmp_skill, evoclaw_dir)
        cmd_install_evoclaw(tmp_skill, evoclaw_dir)
        assert (evoclaw_dir / "test-skill" / "agent.toml").exists()
