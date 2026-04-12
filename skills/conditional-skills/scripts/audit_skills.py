#!/usr/bin/env python3
"""Audit all OpenClaw skills for conditional activation rules."""

import os
import sys

# Add parent scripts to path for reuse
sys.path.insert(0, os.path.dirname(__file__))
from check_conditions import check_conditions


def audit_all_skills(skills_dir: str = None):
    """Scan all skills and report conditional activation status."""
    if skills_dir is None:
        skills_dir = os.path.expanduser("~/.openclaw/workspace/skills")

    if not os.path.isdir(skills_dir):
        print(f"Skills directory not found: {skills_dir}", file=sys.stderr)
        sys.exit(1)

    results = []
    for entry in sorted(os.listdir(skills_dir)):
        skill_dir = os.path.join(skills_dir, entry)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if os.path.isdir(skill_dir) and os.path.exists(skill_md):
            result = check_conditions(skill_dir)
            results.append(result)

    # Print markdown table
    conditional = [r for r in results if r["conditional"]]
    unconditional = [r for r in results if not r["conditional"]]

    print(f"# Skill Activation Audit\n")
    print(f"**Total skills:** {len(results)} | **Conditional:** {len(conditional)} | **Always visible:** {len(unconditional)}\n")

    if conditional:
        print("## Conditional Skills\n")
        print("| Skill | Visible | Reasons |")
        print("|-------|---------|---------|")
        for r in conditional:
            status = "✅ Yes" if r["visible"] else "❌ No"
            reasons = "; ".join(r["reasons"])
            print(f"| {r['skill']} | {status} | {reasons} |")
        print()

    if unconditional:
        print("## Always-Visible Skills\n")
        print("| Skill |")
        print("|-------|")
        for r in unconditional:
            print(f"| {r['skill']} |")


if __name__ == "__main__":
    skills_dir = sys.argv[1] if len(sys.argv) > 1 else None
    audit_all_skills(skills_dir)
