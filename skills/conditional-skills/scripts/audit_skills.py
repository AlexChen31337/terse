#!/usr/bin/env python3
"""
conditional-skills: audit_skills.py
Audit all workspace skills for conditional activation metadata.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SKILLS_DIR = Path.home() / ".openclaw" / "workspace" / "skills"
sys.path.insert(0, str(Path(__file__).parent))
from check_conditions import check_conditions, parse_frontmatter, parse_metadata, extract_openclaw_metadata


def audit_all_skills() -> list[dict]:
    """Audit all skills and return their conditional status."""
    results = []
    if not SKILLS_DIR.exists():
        return results
    
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        
        result = check_conditions(str(skill_dir))
        has_metadata = bool(result.get("checks"))
        results.append({
            "name": skill_dir.name,
            "has_conditions": has_metadata,
            "eligible": result.get("eligible", True),
            "reason": result.get("reason", "No metadata"),
        })
    
    return results


def main():
    as_json = "--json" in sys.argv
    results = audit_all_skills()
    
    conditional = [r for r in results if r["has_conditions"]]
    unconditional = [r for r in results if not r["has_conditions"]]
    hidden = [r for r in results if not r["eligible"]]
    
    if as_json:
        print(json.dumps({
            "total": len(results),
            "conditional": len(conditional),
            "unconditional": len(unconditional),
            "hidden": len(hidden),
            "skills": results
        }, indent=2))
        return
    
    print(f"## Skills Conditional Audit\n")
    print(f"**Total skills:** {len(results)}")
    print(f"**Conditional:** {len(conditional)} | **Unconditional:** {len(unconditional)} | **Hidden (current runtime):** {len(hidden)}\n")
    
    if conditional:
        print("### Conditional Skills\n")
        print("| Skill | Eligible | Reason |")
        print("|-------|----------|--------|")
        for r in conditional:
            status = "✅" if r["eligible"] else "❌"
            print(f"| {r['name']} | {status} | {r['reason']} |")
        print()
    
    if hidden:
        print("### Hidden (not eligible on this runtime)\n")
        for r in hidden:
            print(f"- **{r['name']}**: {r['reason']}")
        print()
    
    print(f"### Unconditional Skills ({len(unconditional)})\n")
    names = [r["name"] for r in unconditional]
    # Print in columns
    col_width = max(len(n) for n in names) + 2 if names else 20
    cols = 4
    for i in range(0, len(names), cols):
        row = names[i:i+cols]
        print("  ".join(n.ljust(col_width) for n in row))


if __name__ == "__main__":
    main()
