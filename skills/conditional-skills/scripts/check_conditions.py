#!/usr/bin/env python3
"""Check conditional activation for a single OpenClaw skill."""

import json
import os
import platform
import re
import sys


def parse_frontmatter(skill_dir: str) -> dict:
    """Parse YAML frontmatter from SKILL.md."""
    skill_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_path):
        return {}

    with open(skill_path) as f:
        content = f.read()

    # Extract YAML between --- markers
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    # Simple YAML parsing (no pyyaml dependency)
    yaml_text = match.group(1)
    result = {}
    current_key = None
    indent_stack = [result]

    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Handle key: value
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()

            if value.startswith("[") and value.endswith("]"):
                # Inline list
                items = [
                    v.strip().strip("\"'")
                    for v in value[1:-1].split(",")
                    if v.strip()
                ]
                indent_stack[-1][key] = items
            elif value:
                indent_stack[-1][key] = value
            else:
                indent_stack[-1][key] = {}
                current_key = key

    return result


def get_metadata(frontmatter: dict) -> dict:
    """Extract openclaw metadata from frontmatter."""
    metadata = frontmatter.get("metadata", {})
    if isinstance(metadata, dict):
        return metadata.get("openclaw", {})
    return {}


def get_available_tools() -> list[str]:
    """Get list of currently available tools (simplified check)."""
    tools = ["exec", "read", "write", "edit", "web_search", "web_fetch", "browser", "memory_search"]
    return tools


def get_available_toolsets() -> list[str]:
    """Get list of currently available toolsets."""
    return ["terminal", "web", "file", "memory", "browser"]


def check_platform(platforms: list[str]) -> tuple[bool, str]:
    """Check if current platform matches."""
    system = platform.system().lower()
    platform_map = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    current = platform_map.get(system, system)

    if current in platforms:
        return True, f"platforms: {current} ∈ {platforms}"
    return False, f"platforms: {current} ∉ {platforms}"


def check_conditions(skill_dir: str) -> dict:
    """Check all conditional activation rules for a skill."""
    frontmatter = parse_frontmatter(skill_dir)
    metadata = get_metadata(frontmatter)

    if not metadata:
        return {
            "visible": True,
            "conditional": False,
            "reasons": ["No conditional fields — always visible"],
            "skill": frontmatter.get("name", os.path.basename(skill_dir)),
        }

    available_tools = get_available_tools()
    available_toolsets = get_available_toolsets()
    visible = True
    reasons = []

    # Check fallback_for_toolsets
    if "fallback_for_toolsets" in metadata:
        needed = metadata["fallback_for_toolsets"]
        if isinstance(needed, list):
            all_available = all(t in available_toolsets for t in needed)
            if all_available:
                visible = False
                reasons.append(f"fallback_for_toolsets: {needed} all available → HIDDEN")
            else:
                reasons.append(f"fallback_for_toolsets: {needed} not all available → SHOWN")

    # Check fallback_for_tools
    if "fallback_for_tools" in metadata:
        needed = metadata["fallback_for_tools"]
        if isinstance(needed, list):
            all_available = all(t in available_tools for t in needed)
            if all_available:
                visible = False
                reasons.append(f"fallback_for_tools: {needed} all available → HIDDEN")
            else:
                reasons.append(f"fallback_for_tools: {needed} not all available → SHOWN")

    # Check requires_toolsets
    if "requires_toolsets" in metadata:
        needed = metadata["requires_toolsets"]
        if isinstance(needed, list):
            all_available = all(t in available_toolsets for t in needed)
            if not all_available:
                visible = False
                reasons.append(f"requires_toolsets: {needed} not all available → HIDDEN")
            else:
                reasons.append(f"requires_toolsets: {needed} all available → SHOWN")

    # Check requires_tools
    if "requires_tools" in metadata:
        needed = metadata["requires_tools"]
        if isinstance(needed, list):
            all_available = all(t in available_tools for t in needed)
            if not all_available:
                visible = False
                reasons.append(f"requires_tools: {needed} not all available → HIDDEN")
            else:
                reasons.append(f"requires_tools: {needed} all available → SHOWN")

    # Check platforms
    if "platforms" in metadata:
        plat_ok, plat_reason = check_platform(metadata["platforms"])
        if not plat_ok:
            visible = False
        reasons.append(plat_reason)

    return {
        "visible": visible,
        "conditional": True,
        "reasons": reasons,
        "skill": frontmatter.get("name", os.path.basename(skill_dir)),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check_conditions.py <skill-directory>", file=sys.stderr)
        sys.exit(1)

    result = check_conditions(sys.argv[1])
    print(json.dumps(result, indent=2))
