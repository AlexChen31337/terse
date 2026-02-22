#!/usr/bin/env python3
"""
skill-bridge — Unified Skill Spec bridge adapter.

Converts between OpenClaw (SKILL.md) and EvoClaw (skill.toml + agent.toml)
skill formats, validates unified skill directories, and installs skills across
runtimes.

Usage:
    uv run python scripts/bridge.py convert-to-evoclaw <skill-dir>
    uv run python scripts/bridge.py convert-to-openclaw <skill-dir>
    uv run python scripts/bridge.py validate <skill-dir>
    uv run python scripts/bridge.py install-evoclaw <skill-dir> <evoclaw-skills-dir>

Exit codes:
    0  Success
    1  Validation failure / nothing to do
    2  Parse error (bad SKILL.md or skill.toml)
    4  Input error (missing file / bad args)
    5  Unexpected internal error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SkillFrontmatter:
    """Parsed YAML-ish frontmatter from SKILL.md."""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = "MIT"
    tags: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    env: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDef:
    """A single tool from [tools.NAME] in skill.toml."""
    name: str
    command: str
    description: str = ""
    args: list[str] = field(default_factory=list)
    env: list[str] = field(default_factory=list)
    timeout_secs: int = 30


@dataclass
class GenomeParam:
    """One evolvable parameter from [genome.params]."""
    key: str
    value: Any
    min: Any | None = None
    max: Any | None = None
    type: str = "float"


@dataclass
class SkillToml:
    """Parsed skill.toml."""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = "MIT"
    repository: str = ""
    homepage: str = ""
    openclaw: bool = True
    evoclaw: bool = True
    clawhub: bool = True
    openclaw_min: str = ""
    evoclaw_min: str = ""
    tags: list[str] = field(default_factory=list)
    python: str = ""
    packages: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    env: list[str] = field(default_factory=list)
    tools: dict[str, ToolDef] = field(default_factory=dict)
    genome_weight: float = 0.5
    genome_enabled: bool = True
    genome_params: dict[str, GenomeParam] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# SKILL.md parsing
# ─────────────────────────────────────────────────────────────────────────────

def parse_skill_md(skill_dir: Path) -> tuple[SkillFrontmatter, str]:
    """
    Parse SKILL.md into frontmatter + body.
    Returns (frontmatter, body_markdown).
    Raises SystemExit(2) on parse error.
    """
    path = skill_dir / "SKILL.md"
    if not path.exists():
        _die(f"SKILL.md not found in {skill_dir}", 4)

    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)

    front = SkillFrontmatter(raw=fm)
    front.name = str(fm.get("name", ""))
    front.version = str(fm.get("version", "1.0.0"))
    front.description = str(fm.get("description", ""))
    front.author = str(fm.get("author", ""))
    front.license = str(fm.get("license", "MIT"))

    # tags can be at top level or inside frontmatter
    raw_tags = fm.get("tags", [])
    if isinstance(raw_tags, list):
        front.tags = [str(t) for t in raw_tags]

    # metadata.evoclaw.permissions / env
    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        evoclaw_meta = meta.get("evoclaw", {})
        if isinstance(evoclaw_meta, dict):
            perms = evoclaw_meta.get("permissions", [])
            front.permissions = list(perms) if isinstance(perms, list) else []
            env = evoclaw_meta.get("env", [])
            front.env = list(env) if isinstance(env, list) else []

    return front, body


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split SKILL.md into (frontmatter_dict, body). Handles --- delimiters."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break

    if end is None:
        return {}, text

    yaml_block = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:]).lstrip("\n")
    fm = _parse_simple_yaml(yaml_block)
    return fm, body


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """
    Minimal YAML parser for SKILL.md frontmatter.
    Handles: string scalars, inline lists, nested dicts (2-space indent), list items (- item).
    Falls back to pyyaml if available.
    """
    try:
        import yaml  # type: ignore[import]
        return yaml.safe_load(text) or {}
    except ImportError:
        pass

    # Fallback: hand-rolled minimal parser with lookahead.
    # We pre-process lines into tokens, then walk with lookahead to decide
    # whether an empty-value key starts a dict or a list.
    result: dict[str, Any] = {}
    non_empty = [
        (len(l) - len(l.lstrip()), l.strip())
        for l in text.splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]

    # stack: list of (indent, dict) pairs
    dict_stack: list[tuple[int, dict[str, Any]]] = [(-1, result)]
    # Maps indent level → active list at that indent (for "- item" lines)
    active_lists: dict[int, list[Any]] = {}
    # Maps indent level → (key, parent_dict) for deferred list creation
    pending_list_key: dict[int, tuple[str, dict[str, Any]]] = {}

    i = 0
    while i < len(non_empty):
        indent, stripped = non_empty[i]

        # Pop dict stack back to a level whose indent is strictly less than current
        while len(dict_stack) > 1 and dict_stack[-1][0] >= indent:
            dict_stack.pop()

        # Clear active lists that are no longer in scope
        active_lists = {k: v for k, v in active_lists.items() if k <= indent}

        current_dict = dict_stack[-1][1]

        # ── YAML list item ────────────────────────────────────────────────
        if stripped.startswith("- "):
            val = stripped[2:].strip().strip('"').strip("'")
            lst = active_lists.get(indent)
            if lst is None:
                # No active list at this indent — check if there's a pending key
                # for the parent indent (indent - 2)
                pending = pending_list_key.pop(indent, None)
                if pending:
                    key, parent = pending
                    new_list: list[Any] = [val]
                    parent[key] = new_list
                    active_lists[indent] = new_list
                # else orphan — skip
            else:
                lst.append(val)
            i += 1
            continue

        if ":" not in stripped:
            i += 1
            continue

        key, _, raw_val = stripped.partition(":")
        key = key.strip()
        val = raw_val.strip()

        if not val or val == ">":
            # Peek at next non-empty line to decide: dict or list?
            next_indent, next_stripped = (
                non_empty[i + 1] if i + 1 < len(non_empty) else (indent, "")
            )
            if next_stripped.startswith("- ") and next_indent > indent:
                # It's a list — register as pending; the "- item" handler will populate it
                pending_list_key[next_indent] = (key, current_dict)
            else:
                # It's a nested dict
                new_dict: dict[str, Any] = {}
                current_dict[key] = new_dict
                dict_stack.append((indent, new_dict))
        elif val.startswith("[") and val.endswith("]"):
            # Inline list
            inner = val[1:-1]
            items = [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]
            current_dict[key] = items
        else:
            # Scalar — strip quotes
            current_dict[key] = val.strip('"').strip("'")

        i += 1

    return result


# ─────────────────────────────────────────────────────────────────────────────
# skill.toml parsing
# ─────────────────────────────────────────────────────────────────────────────

def parse_skill_toml(skill_dir: Path) -> SkillToml:
    """
    Parse skill.toml into a SkillToml dataclass.
    Raises SystemExit(2) on parse error, SystemExit(4) if missing.
    """
    path = skill_dir / "skill.toml"
    if not path.exists():
        _die(f"skill.toml not found in {skill_dir}", 4)

    try:
        import tomllib  # Python 3.11+
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[import,no-redef]
            with open(path, "rb") as f:
                raw = tomllib.load(f)
        except ImportError:
            # Final fallback: minimal hand-rolled parser
            raw = _parse_minimal_toml(path.read_text(encoding="utf-8"))

    st = SkillToml()
    skill_sec = raw.get("skill", {})
    st.name = str(skill_sec.get("name", ""))
    st.version = str(skill_sec.get("version", "1.0.0"))
    st.description = str(skill_sec.get("description", ""))
    st.author = str(skill_sec.get("author", ""))
    st.license = str(skill_sec.get("license", "MIT"))
    st.repository = str(skill_sec.get("repository", ""))
    st.homepage = str(skill_sec.get("homepage", ""))

    compat = skill_sec.get("compat", {})
    st.openclaw = bool(compat.get("openclaw", True))
    st.evoclaw = bool(compat.get("evoclaw", True))
    st.clawhub = bool(compat.get("clawhub", True))
    st.openclaw_min = str(compat.get("openclaw_min", ""))
    st.evoclaw_min = str(compat.get("evoclaw_min", ""))

    tags_sec = skill_sec.get("tags", {})
    if isinstance(tags_sec, dict):
        raw_tags = tags_sec.get("tags", [])
    else:
        raw_tags = []
    st.tags = list(raw_tags) if isinstance(raw_tags, list) else []

    deps = skill_sec.get("deps", {})
    st.python = str(deps.get("python", ""))
    pkgs = deps.get("packages", [])
    st.packages = list(pkgs) if isinstance(pkgs, list) else []

    evoclaw_sec = skill_sec.get("evoclaw", {})
    perms = evoclaw_sec.get("permissions", [])
    st.permissions = list(perms) if isinstance(perms, list) else []
    env = evoclaw_sec.get("env", [])
    st.env = list(env) if isinstance(env, list) else []

    # Tools
    tools_raw = raw.get("tools", {})
    for tool_name, tool_data in tools_raw.items():
        if not isinstance(tool_data, dict):
            continue
        td = ToolDef(
            name=tool_name,
            command=str(tool_data.get("command", "")),
            description=str(tool_data.get("description", "")),
            args=list(tool_data.get("args", [])),
            env=list(tool_data.get("env", [])),
            timeout_secs=int(tool_data.get("timeout_secs", 30)),
        )
        st.tools[tool_name] = td

    # Genome
    genome_sec = raw.get("genome", {})
    st.genome_weight = float(genome_sec.get("weight", 0.5))
    st.genome_enabled = bool(genome_sec.get("enabled", True))
    params_raw = genome_sec.get("params", {})
    for pk, pv in params_raw.items():
        if isinstance(pv, dict):
            gp = GenomeParam(
                key=pk,
                value=pv.get("value"),
                min=pv.get("min"),
                max=pv.get("max"),
                type=str(pv.get("type", "float")),
            )
        else:
            gp = GenomeParam(key=pk, value=pv)
        st.genome_params[pk] = gp

    return st


def _parse_minimal_toml(text: str) -> dict[str, Any]:
    """
    Ultra-minimal TOML parser that handles the subset used in skill.toml.
    Handles: [section], [section.sub], key = "value", key = true/false/123,
             key = ["a", "b"], inline dicts {k=v, ...}.
    NOT a full TOML implementation.
    """
    result: dict[str, Any] = {}
    current_path: list[str] = []

    def get_or_create(path: list[str]) -> dict[str, Any]:
        node = result
        for part in path:
            node = node.setdefault(part, {})
        return node  # type: ignore[return-value]

    def parse_value(raw: str) -> Any:
        raw = raw.strip()
        # Quoted string — find the matching close quote, ignoring trailing comments
        if raw.startswith('"'):
            # Find close quote (first unescaped " after position 0)
            close = raw.find('"', 1)
            if close != -1:
                return raw[1:close]
            return raw.strip('"')
        if raw.startswith("'"):
            close = raw.find("'", 1)
            if close != -1:
                return raw[1:close]
            return raw.strip("'")
        if raw.lower() == "true":
            return True
        if raw.lower() == "false":
            return False
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            if not inner:
                return []
            items = []
            for item in _split_toml_array(inner):
                items.append(parse_value(item.strip()))
            return items
        if raw.startswith("{") and raw.endswith("}"):
            inner = raw[1:-1].strip()
            d: dict[str, Any] = {}
            for pair in _split_toml_array(inner):
                if "=" in pair:
                    k, _, v = pair.partition("=")
                    d[k.strip()] = parse_value(v.strip())
            return d
        # Strip trailing inline comment for bare values
        if "#" in raw:
            raw = raw[: raw.index("#")].strip()
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            pass
        return raw

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            # Section header — strip brackets, handle [[...]] as [...]
            header = re.sub(r"^\[+|\]+$", "", line)
            current_path = [p.strip() for p in header.split(".")]
            get_or_create(current_path)
            continue
        if "=" in line:
            eq = line.index("=")
            key = line[:eq].strip()
            val = line[eq + 1:].strip()
            # Strip inline comments (simple heuristic)
            if "#" in val and not (val.startswith('"') or val.startswith("'")):
                val = val[: val.index("#")].strip()
            get_or_create(current_path)[key] = parse_value(val)

    return result


def _split_toml_array(s: str) -> list[str]:
    """Split a comma-separated TOML array body, respecting nested brackets/quotes."""
    parts = []
    depth = 0
    in_str = False
    buf = ""
    for ch in s:
        if ch == '"' and not in_str:
            in_str = True
            buf += ch
        elif ch == '"' and in_str:
            in_str = False
            buf += ch
        elif ch in "[{(" and not in_str:
            depth += 1
            buf += ch
        elif ch in "]}" and not in_str:
            depth -= 1
            buf += ch
        elif ch == "," and depth == 0 and not in_str:
            parts.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf.strip())
    return parts


# ─────────────────────────────────────────────────────────────────────────────
# Generators
# ─────────────────────────────────────────────────────────────────────────────

def generate_skill_toml(fm: SkillFrontmatter, skill_dir: Path) -> str:
    """Generate a skill.toml from a parsed SKILL.md frontmatter."""
    tags_str = ", ".join(f'"{t}"' for t in fm.tags) if fm.tags else ""
    perms_str = ", ".join(f'"{p}"' for p in fm.permissions) if fm.permissions else ""
    env_str = ", ".join(f'"{e}"' for e in fm.env) if fm.env else ""

    # Discover scripts
    scripts_dir = skill_dir / "scripts"
    tool_sections = ""
    if scripts_dir.exists():
        for py_file in sorted(scripts_dir.glob("*.py")):
            tool_name = py_file.stem.replace("_", "-")
            tool_sections += textwrap.dedent(f"""
                [tools.{tool_name}]
                command     = "uv run python scripts/{py_file.name}"
                description = "{tool_name} tool"
                timeout_secs = 30
            """)

    genome_section = textwrap.dedent("""
        [genome]
        weight  = 0.5
        enabled = true

        # [genome.params]
        # param_name = { value = 10, min = 1, max = 100, type = "int" }
    """)

    return textwrap.dedent(f"""\
        [skill]
        name        = "{fm.name}"
        version     = "{fm.version}"
        description = "{fm.description}"
        author      = "{fm.author}"
        license     = "{fm.license}"

        [skill.compat]
        openclaw = true
        evoclaw  = true
        clawhub  = true

        [skill.tags]
        tags = [{tags_str}]

        [skill.deps]
        python = ">=3.11"
        # packages = []

        [skill.evoclaw]
        permissions = [{perms_str}]
        env         = [{env_str}]
        {tool_sections}
        {genome_section}
    """)


def generate_skill_md(st: SkillToml) -> str:
    """Generate a SKILL.md from a parsed SkillToml."""
    perms_yaml = "\n".join(f"      - {p}" for p in st.permissions) if st.permissions else ""
    env_yaml = "\n".join(f"      - {e}" for e in st.env) if st.env else ""

    evoclaw_meta = ""
    if st.permissions or st.env:
        evoclaw_meta = "metadata:\n  evoclaw:"
        if st.permissions:
            evoclaw_meta += "\n    permissions:\n" + perms_yaml
        if st.env:
            evoclaw_meta += "\n    env:\n" + env_yaml

    tags_yaml = ""
    if st.tags:
        tags_yaml = "tags: [" + ", ".join(st.tags) + "]"

    tools_doc = ""
    for name, tool in st.tools.items():
        tools_doc += f"\n### `{name}`\n\n"
        tools_doc += f"{tool.description}\n\n"
        tools_doc += f"```bash\n{tool.command}"
        if tool.args:
            tools_doc += " " + " ".join(tool.args)
        tools_doc += "\n```\n"

    return textwrap.dedent(f"""\
        ---
        name: {st.name}
        version: {st.version}
        description: "{st.description}"
        author: "{st.author}"
        license: {st.license}
        {tags_yaml}
        {evoclaw_meta}
        ---

        # {st.name} — Agent Skill

        {st.description}

        ## When to Use

        <!-- TODO: describe trigger phrases and automatic triggers -->

        ## Quick Start

        ```bash
        # TODO: add quick-start commands
        ```

        ## Tools
        {tools_doc}

        ## Output Format

        <!-- TODO: describe JSON output schema -->

        ## Configuration

        **Required environment variables:**
        {chr(10).join(f"- `{e}`" for e in st.env) if st.env else "None"}

        ## Links

        {"- **Repository:** " + st.repository if st.repository else ""}
        {"- **Homepage:** " + st.homepage if st.homepage else ""}
    """)


def generate_agent_toml(st: SkillToml) -> str:
    """
    Generate agent.toml content (EvoClaw tool definitions only).
    This is the file EvoClaw's ParseToolsTOML reads.
    """
    if not st.tools:
        return "# No tools defined for this skill.\n"

    lines = [
        "# agent.toml — generated by skill-bridge from skill.toml",
        f"# Skill: {st.name} v{st.version}",
        "# DO NOT EDIT — regenerate with: bridge.py install-evoclaw",
        "",
    ]
    for tool in st.tools.values():
        lines.append(f"[tools.{tool.name}]")
        lines.append(f'command     = "{tool.command}"')
        lines.append(f'description = "{tool.description}"')
        if tool.args:
            args_str = ", ".join(f'"{a}"' for a in tool.args)
            lines.append(f"args        = [{args_str}]")
        if tool.env:
            env_str = ", ".join(f'"{e}"' for e in tool.env)
            lines.append(f"env         = [{env_str}]")
        lines.append(f"timeout_secs = {tool.timeout_secs}")
        lines.append("")

    return "\n".join(lines)


def generate_genome_json(st: SkillToml) -> dict[str, Any]:
    """
    Build a SkillGenome JSON dict for EvoClaw direct genome injection.
    Matches internal/genome.SkillGenome struct.
    """
    params: dict[str, Any] = {}
    for pk, gp in st.genome_params.items():
        params[pk] = gp.value

    return {
        "enabled": st.genome_enabled,
        "weight": st.genome_weight,
        "params": params,
        "fitness": 0.0,
        "version": 1,
        "eval_count": 0,
        "verified": False,
        "vfm_score": 0.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def report(self) -> None:
        if self.errors:
            print("❌ Errors:")
            for e in self.errors:
                print(f"   • {e}")
        if self.warnings:
            print("⚠️  Warnings:")
            for w in self.warnings:
                print(f"   • {w}")
        if self.ok:
            print("✅ Validation passed")
            if self.warnings:
                print(f"   ({len(self.warnings)} warning(s))")


def validate_skill(skill_dir: Path) -> ValidationResult:
    """Validate a unified skill directory for consistency and completeness."""
    vr = ValidationResult()
    skill_dir = skill_dir.resolve()

    if not skill_dir.exists():
        vr.error(f"Directory does not exist: {skill_dir}")
        return vr

    # ── SKILL.md ──────────────────────────────────────────────────────────────
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        vr.error("SKILL.md is missing")
    else:
        try:
            fm, body = parse_skill_md(skill_dir)
            if not fm.name:
                vr.error("SKILL.md frontmatter: 'name' is required")
            if not fm.version:
                vr.warn("SKILL.md frontmatter: 'version' not set")
            if not fm.description:
                vr.warn("SKILL.md frontmatter: 'description' not set")
            if not fm.author:
                vr.warn("SKILL.md frontmatter: 'author' not set")
            if len(body.strip()) < 50:
                vr.warn("SKILL.md body is very short — consider adding documentation")
        except SystemExit:
            vr.error("SKILL.md could not be parsed")

    # ── skill.toml ────────────────────────────────────────────────────────────
    skill_toml_path = skill_dir / "skill.toml"
    if not skill_toml_path.exists():
        vr.error("skill.toml is missing")
    else:
        try:
            st = parse_skill_toml(skill_dir)
            if not st.name:
                vr.error("skill.toml [skill]: 'name' is required")
            if not st.version:
                vr.warn("skill.toml [skill]: 'version' not set")

            # Cross-check name consistency
            if skill_md.exists():
                try:
                    fm2, _ = parse_skill_md(skill_dir)
                    if fm2.name and st.name and fm2.name != st.name:
                        vr.error(
                            f"Name mismatch: SKILL.md says '{fm2.name}', "
                            f"skill.toml says '{st.name}'"
                        )
                    if fm2.version and st.version and fm2.version != st.version:
                        vr.warn(
                            f"Version mismatch: SKILL.md says '{fm2.version}', "
                            f"skill.toml says '{st.version}'"
                        )
                except SystemExit:
                    pass

            # EvoClaw-specific checks
            if st.evoclaw:
                if not st.tools:
                    vr.warn(
                        "skill.toml: evoclaw=true but no [tools.*] sections defined. "
                        "EvoClaw agents will have no callable tools from this skill."
                    )
                for name, tool in st.tools.items():
                    if not tool.command:
                        vr.error(f"[tools.{name}]: 'command' is required")
                    if not tool.description:
                        vr.warn(f"[tools.{name}]: 'description' is empty")

            # Genome bounds check
            for pk, gp in st.genome_params.items():
                if gp.min is not None and gp.max is not None:
                    if gp.value is not None:
                        try:
                            v, lo, hi = float(gp.value), float(gp.min), float(gp.max)
                            if not (lo <= v <= hi):
                                vr.warn(
                                    f"[genome.params.{pk}]: value={gp.value} is outside "
                                    f"bounds [{gp.min}, {gp.max}]"
                                )
                        except (TypeError, ValueError):
                            pass

        except SystemExit:
            vr.error("skill.toml could not be parsed")

    # ── Scripts ───────────────────────────────────────────────────────────────
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        vr.warn("No scripts/ directory — this skill has no executable tools")
    else:
        py_files = list(scripts_dir.glob("*.py"))
        if not py_files:
            vr.warn("scripts/ directory is empty")

    # ── Tests ─────────────────────────────────────────────────────────────────
    tests_dir = skill_dir / "tests"
    if not tests_dir.exists():
        vr.warn("No tests/ directory — ClawInfra standards require tests")
    else:
        test_files = list(tests_dir.glob("test_*.py"))
        if not test_files:
            vr.warn("tests/ directory has no test_*.py files")

    return vr


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

def cmd_convert_to_evoclaw(skill_dir: Path) -> None:
    """
    Read SKILL.md → generate skill.toml (plus update SKILL.md frontmatter with
    evoclaw metadata if not already present).
    """
    skill_dir = skill_dir.resolve()
    print(f"Converting {skill_dir.name} → EvoClaw format...")

    fm, body = parse_skill_md(skill_dir)

    toml_path = skill_dir / "skill.toml"
    if toml_path.exists():
        print(f"  skill.toml already exists — merging name/version from SKILL.md")
        st = parse_skill_toml(skill_dir)
        # Update name/version if SKILL.md has them and toml doesn't
        if fm.name and not st.name:
            print(f"  → Setting name = {fm.name!r}")
        if fm.tags and not st.tags:
            print(f"  → Adding tags from SKILL.md: {fm.tags}")
    else:
        print(f"  Generating skill.toml...")
        toml_content = generate_skill_toml(fm, skill_dir)
        toml_path.write_text(toml_content, encoding="utf-8")
        print(f"  ✅ Written: skill.toml")

    # Ensure SKILL.md frontmatter has the full EvoClaw fields
    _ensure_frontmatter_evoclaw(skill_dir, fm, body)

    print(f"\nDone. Run `bridge.py validate {skill_dir}` to check.")


def cmd_convert_to_openclaw(skill_dir: Path) -> None:
    """Read skill.toml → generate/update SKILL.md."""
    skill_dir = skill_dir.resolve()
    print(f"Converting {skill_dir.name} → OpenClaw format...")

    st = parse_skill_toml(skill_dir)

    skill_md_path = skill_dir / "SKILL.md"
    if skill_md_path.exists():
        print("  SKILL.md already exists — updating frontmatter only")
        fm, body = parse_skill_md(skill_dir)
        # Update frontmatter fields from toml
        fm.name = fm.name or st.name
        fm.version = st.version  # toml is authoritative
        fm.description = fm.description or st.description
        fm.author = fm.author or st.author
        fm.license = fm.license or st.license
        if not fm.permissions and st.permissions:
            fm.permissions = st.permissions
        if not fm.env and st.env:
            fm.env = st.env
        if not fm.tags and st.tags:
            fm.tags = st.tags
        _write_skill_md(skill_md_path, fm, body)
        print(f"  ✅ Updated: SKILL.md")
    else:
        print("  Generating SKILL.md...")
        md_content = generate_skill_md(st)
        skill_md_path.write_text(md_content, encoding="utf-8")
        print(f"  ✅ Written: SKILL.md")

    print(f"\nDone. Run `bridge.py validate {skill_dir}` to check.")


def cmd_validate(skill_dir: Path) -> None:
    """Validate a unified skill directory."""
    skill_dir = skill_dir.resolve()
    print(f"Validating: {skill_dir}\n")
    vr = validate_skill(skill_dir)
    vr.report()
    sys.exit(0 if vr.ok else 1)


def cmd_install_evoclaw(skill_dir: Path, evoclaw_skills_dir: Path) -> None:
    """
    Install an OpenClaw/unified skill into EvoClaw's skills directory.

    Steps:
    1. Validate the skill
    2. Copy skill directory to <evoclaw-skills-dir>/<skill-name>/
    3. Generate agent.toml from [tools.*] in skill.toml
    4. Generate genome.json for direct genome injection (optional)
    """
    skill_dir = skill_dir.resolve()
    evoclaw_skills_dir = evoclaw_skills_dir.resolve()

    print(f"Installing {skill_dir.name} → {evoclaw_skills_dir}/...")

    # Validate first
    vr = validate_skill(skill_dir)
    if not vr.ok:
        print("\n❌ Validation failed — fix errors before installing:")
        vr.report()
        sys.exit(1)
    if vr.warnings:
        print("⚠️  Warnings (non-fatal):")
        for w in vr.warnings:
            print(f"   • {w}")

    # Load metadata
    try:
        st = parse_skill_toml(skill_dir)
    except SystemExit:
        # skill.toml may not exist yet — try to generate from SKILL.md
        fm, _ = parse_skill_md(skill_dir)
        print("  No skill.toml found — generating from SKILL.md first...")
        toml_content = generate_skill_toml(fm, skill_dir)
        (skill_dir / "skill.toml").write_text(toml_content, encoding="utf-8")
        st = parse_skill_toml(skill_dir)

    dest = evoclaw_skills_dir / st.name
    if dest.exists():
        print(f"  Removing existing installation at {dest}")
        shutil.rmtree(dest)

    evoclaw_skills_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Copying skill directory → {dest}")
    shutil.copytree(skill_dir, dest, ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc"))

    # Generate agent.toml
    agent_toml_content = generate_agent_toml(st)
    agent_toml_path = dest / "agent.toml"
    agent_toml_path.write_text(agent_toml_content, encoding="utf-8")
    print(f"  ✅ Generated: agent.toml ({len(st.tools)} tool(s))")

    # Generate genome.json (optional — for direct injection into EvoClaw)
    if st.genome_params or st.genome_weight != 0.5:
        genome_data = generate_genome_json(st)
        genome_path = dest / "genome.json"
        genome_path.write_text(json.dumps(genome_data, indent=2), encoding="utf-8")
        print(f"  ✅ Generated: genome.json ({len(st.genome_params)} evolvable param(s))")

    print(f"\n✅ Installed {st.name} v{st.version} → {dest}")
    print(f"   EvoClaw will pick this up on next skill reload.")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_frontmatter_evoclaw(
    skill_dir: Path, fm: SkillFrontmatter, body: str
) -> None:
    """Make sure SKILL.md frontmatter has EvoClaw-required fields."""
    path = skill_dir / "SKILL.md"
    changed = False

    if not fm.version:
        fm.version = "1.0.0"
        changed = True

    if not fm.permissions and not fm.env:
        # No evoclaw metadata yet — don't force it, just warn
        pass

    if changed:
        _write_skill_md(path, fm, body)
        print("  ✅ Updated SKILL.md frontmatter")


def _write_skill_md(path: Path, fm: SkillFrontmatter, body: str) -> None:
    """Overwrite SKILL.md with updated frontmatter."""
    perms_yaml = ""
    if fm.permissions:
        items = "\n".join(f"      - {p}" for p in fm.permissions)
        perms_yaml = f"\n    permissions:\n{items}"
    env_yaml = ""
    if fm.env:
        items = "\n".join(f"      - {e}" for e in fm.env)
        env_yaml = f"\n    env:\n{items}"

    evoclaw_block = ""
    if perms_yaml or env_yaml:
        evoclaw_block = f"metadata:\n  evoclaw:{perms_yaml}{env_yaml}\n"

    tags_line = ""
    if fm.tags:
        tags_line = "tags: [" + ", ".join(fm.tags) + "]\n"

    frontmatter_lines = [
        "---",
        f"name: {fm.name}",
        f"version: {fm.version}",
        f'description: "{fm.description}"',
        f'author: "{fm.author}"',
        f"license: {fm.license}",
    ]
    if tags_line.strip():
        frontmatter_lines.append(tags_line.rstrip())
    if evoclaw_block.strip():
        frontmatter_lines.append(evoclaw_block.rstrip())
    frontmatter_lines.append("---")

    content = "\n".join(frontmatter_lines) + "\n\n" + body
    path.write_text(content, encoding="utf-8")


def _die(msg: str, code: int = 5) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bridge.py",
        description="Unified Skill Spec bridge adapter — convert and install skills across runtimes.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # convert-to-evoclaw
    p_cte = sub.add_parser(
        "convert-to-evoclaw",
        help="Read SKILL.md, generate skill.toml for EvoClaw",
    )
    p_cte.add_argument("skill_dir", type=Path, help="Path to skill directory")

    # convert-to-openclaw
    p_cto = sub.add_parser(
        "convert-to-openclaw",
        help="Read skill.toml, generate/update SKILL.md for OpenClaw",
    )
    p_cto.add_argument("skill_dir", type=Path, help="Path to skill directory")

    # validate
    p_val = sub.add_parser(
        "validate",
        help="Validate both SKILL.md and skill.toml are present and consistent",
    )
    p_val.add_argument("skill_dir", type=Path, help="Path to skill directory")

    # install-evoclaw
    p_ins = sub.add_parser(
        "install-evoclaw",
        help="Install an OpenClaw skill into EvoClaw's skills directory",
    )
    p_ins.add_argument("skill_dir", type=Path, help="Path to skill directory")
    p_ins.add_argument(
        "evoclaw_skills_dir",
        type=Path,
        help="EvoClaw skills directory (e.g. ~/.evoclaw/skills)",
    )

    args = parser.parse_args()

    if args.command == "convert-to-evoclaw":
        cmd_convert_to_evoclaw(args.skill_dir)
    elif args.command == "convert-to-openclaw":
        cmd_convert_to_openclaw(args.skill_dir)
    elif args.command == "validate":
        cmd_validate(args.skill_dir)
    elif args.command == "install-evoclaw":
        cmd_install_evoclaw(args.skill_dir, args.evoclaw_skills_dir)
    else:
        parser.print_help()
        sys.exit(4)


if __name__ == "__main__":
    main()
