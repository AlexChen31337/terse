#!/usr/bin/env python3
"""
conditional-skills: check_conditions.py
Validates a skill's metadata.openclaw conditional block and checks if current runtime meets requirements.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


def parse_frontmatter(content: str) -> dict[str, str]:
    """Extract YAML frontmatter key-value pairs."""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}
    
    fm: dict[str, str] = {}
    current_key = ""
    current_value_lines: list[str] = []
    in_multiline = False
    
    for line in lines[1:end_idx]:
        if in_multiline:
            if line.strip().endswith('"') or (line.strip() and not line.startswith(" ") and not line.startswith("-")):
                current_value_lines.append(line)
                fm[current_key] = "\n".join(current_value_lines)
                in_multiline = False
            else:
                current_value_lines.append(line)
            continue
        
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value.startswith("|") or value.startswith(">"):
                in_multiline = True
                current_key = key
                current_value_lines = []
            elif value:
                fm[key] = value.strip("\"'")
            else:
                fm[key] = ""
    
    return fm


def parse_metadata(metadata_raw: str) -> dict[str, Any] | None:
    """Parse the metadata JSON5/JSON block."""
    if not metadata_raw:
        return None
    try:
        # Try standard JSON first
        return json.loads(metadata_raw)
    except json.JSONDecodeError:
        pass
    # Try stripping trailing commas
    cleaned = metadata_raw.rstrip().rstrip(",")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Simple JSON5: strip comments, trailing commas
    lines = []
    for line in cleaned.split("\n"):
        stripped = line.split("//")[0] if "//" in line else line
        lines.append(stripped)
    text = "\n".join(lines)
    import re
    text = re.sub(r',\s*([}\]])', r'\1', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_openclaw_metadata(metadata: dict) -> dict | None:
    """Extract the openclaw sub-block from parsed metadata."""
    if not metadata:
        return None
    # Check for openclaw key (any case variations)
    for key in ("openclaw", "openClaw", "OpenClaw"):
        if key in metadata:
            return metadata[key]
    # Legacy keys
    for key in ("open-claw", "oc"):
        if key in metadata:
            return metadata[key]
    return None


def check_bin(bin_name: str) -> bool:
    """Check if a binary exists in PATH."""
    return shutil.which(bin_name) is not None


def check_env(env_name: str) -> bool:
    """Check if an environment variable is set."""
    return bool(os.environ.get(env_name))


def check_conditions(skill_dir: str) -> dict:
    """Check a skill's conditional activation against current runtime."""
    skill_path = Path(skill_dir)
    skill_md = skill_path / "SKILL.md"
    
    if not skill_md.exists():
        return {"error": f"No SKILL.md found at {skill_md}", "eligible": False}
    
    content = skill_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)
    
    if "metadata" not in fm:
        return {
            "skill": skill_path.name,
            "eligible": True,
            "reason": "No conditional metadata — always shown",
            "checks": {}
        }
    
    parsed = parse_metadata(fm["metadata"])
    if not parsed:
        return {
            "skill": skill_path.name,
            "eligible": True,
            "reason": "Could not parse metadata JSON — treating as unconditional",
            "raw_metadata": fm["metadata"][:100],
            "checks": {}
        }
    
    oc = extract_openclaw_metadata(parsed)
    if not oc:
        return {
            "skill": skill_path.name,
            "eligible": True,
            "reason": "No openclaw block in metadata — always shown",
            "checks": {}
        }
    
    checks: dict[str, Any] = {"metadata": oc}
    eligible = True
    reasons: list[str] = []
    
    # OS check
    os_list = oc.get("os", [])
    if os_list:
        import platform
        current_os = platform.system().lower()
        # Map Node.js platform names
        os_map = {"linux": "linux", "darwin": "darwin", "macos": "darwin", "windows": "win32", "win32": "win32"}
        current_node = os_map.get(current_os, current_os)
        matched = any(os_map.get(o.lower(), o.lower()) == current_node for o in os_list)
        checks["os"] = {"required": os_list, "current": current_os, "pass": matched}
        if not matched:
            eligible = False
            reasons.append(f"OS mismatch: need {os_list}, got {current_os}")
    
    # Always bypass
    if oc.get("always") is True:
        return {
            "skill": skill_path.name,
            "eligible": True,
            "reason": "always=true — skip requires checks",
            "checks": checks
        }
    
    requires = oc.get("requires", {})
    
    # bins check
    bins = requires.get("bins", [])
    if bins:
        bin_results = {b: check_bin(b) for b in bins}
        all_present = all(bin_results.values())
        checks["bins"] = {"required": bins, "results": bin_results, "pass": all_present}
        if not all_present:
            eligible = False
            missing = [b for b, found in bin_results.items() if not found]
            reasons.append(f"Missing bins: {missing}")
    
    # anyBins check
    any_bins = requires.get("anyBins", [])
    if any_bins:
        any_results = {b: check_bin(b) for b in any_bins}
        any_present = any(any_results.values())
        checks["anyBins"] = {"required": any_bins, "results": any_results, "pass": any_present}
        if not any_present:
            eligible = False
            reasons.append(f"No required bin found from: {any_bins}")
    
    # env check
    envs = requires.get("env", [])
    if envs:
        env_results = {e: check_env(e) for e in envs}
        all_set = all(env_results.values())
        checks["env"] = {"required": envs, "results": env_results, "pass": all_set}
        if not all_set:
            eligible = False
            missing = [e for e, found in env_results.items() if not found]
            reasons.append(f"Missing env vars: {missing}")
    
    # config check (we can't fully verify this outside OpenClaw runtime)
    configs = requires.get("config", [])
    if configs:
        checks["config"] = {"required": configs, "pass": "unknown — requires OpenClaw runtime"}
    
    return {
        "skill": skill_path.name,
        "eligible": eligible,
        "reason": "; ".join(reasons) if reasons else "All checks passed",
        "checks": checks
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: check_conditions.py <skill-dir> [--json]")
        sys.exit(1)
    
    skill_dir = sys.argv[1]
    as_json = "--json" in sys.argv
    
    result = check_conditions(skill_dir)
    
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"## {result.get('skill', 'unknown')}")
        print(f"**Eligible:** {'✅ YES' if result.get('eligible') else '❌ NO'}")
        print(f"**Reason:** {result.get('reason', 'unknown')}")
        if result.get("checks"):
            print(f"\n**Checks:**")
            for key, val in result["checks"].items():
                if isinstance(val, dict):
                    print(f"  - {key}: {val}")
                else:
                    print(f"  - {key}: {val}")


if __name__ == "__main__":
    main()
