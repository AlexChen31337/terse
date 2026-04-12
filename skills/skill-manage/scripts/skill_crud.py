#!/usr/bin/env python3
"""Skill CRUD operations for OpenClaw agent procedural memory."""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime

SKILLS_DIR = os.path.expanduser("~/.openclaw/workspace/skills")
ARCHIVE_DIR = os.path.join(SKILLS_DIR, ".archive")
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "SKILL_TEMPLATE.md")


def parse_frontmatter(filepath: str) -> dict:
    """Parse YAML frontmatter from a SKILL.md file."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath) as f:
        content = f.read()
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    result = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip("\"'")
    return result


def cmd_create(args):
    """Create a new skill from template."""
    skill_dir = os.path.join(SKILLS_DIR, args.name)
    if os.path.exists(skill_dir):
        print(f"❌ Skill '{args.name}' already exists at {skill_dir}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(skill_dir, exist_ok=True)

    # Read template
    if os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH) as f:
            template = f.read()
    else:
        template = "---\nname: SKILL_NAME\ndescription: \"SKILL_DESCRIPTION\"\nversion: 1.0.0\n---\n\n# SKILL_NAME\n\n## When to Use\n\n## Procedure\n\n## Pitfalls\n\n## Verification\n"

    # Replace placeholders
    content = template.replace("SKILL_NAME", args.name)
    desc = args.description or f"Description for {args.name}"
    content = content.replace("Brief description of what this skill does.", desc)
    content = content.replace("SKILL_DESCRIPTION", desc)

    skill_path = os.path.join(skill_dir, "SKILL.md")
    with open(skill_path, "w") as f:
        f.write(content)

    # Create optional subdirs
    for subdir in ["scripts", "references", "templates"]:
        os.makedirs(os.path.join(skill_dir, subdir), exist_ok=True)
        # Add .gitkeep
        gitkeep = os.path.join(skill_dir, subdir, ".gitkeep")
        open(gitkeep, "w").close()

    print(f"✅ Created skill '{args.name}' at {skill_dir}")
    print(f"   Edit {skill_path} to fill in the details.")


def cmd_delete(args):
    """Archive a skill (soft delete)."""
    skill_dir = os.path.join(SKILLS_DIR, args.name)
    if not os.path.exists(skill_dir):
        print(f"❌ Skill '{args.name}' not found at {skill_dir}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    archive_dest = os.path.join(ARCHIVE_DIR, f"{args.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.move(skill_dir, archive_dest)
    print(f"✅ Archived '{args.name}' → {archive_dest}")


def cmd_list(args):
    """List all active skills."""
    if not os.path.isdir(SKILLS_DIR):
        print("No skills directory found.", file=sys.stderr)
        sys.exit(1)

    skills = []
    for entry in sorted(os.listdir(SKILLS_DIR)):
        if entry.startswith("."):
            continue
        skill_dir = os.path.join(SKILLS_DIR, entry)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if os.path.isdir(skill_dir) and os.path.exists(skill_md):
            fm = parse_frontmatter(skill_md)
            has_scripts = os.path.isdir(os.path.join(skill_dir, "scripts")) and \
                any(f.endswith(".py") for f in os.listdir(os.path.join(skill_dir, "scripts")) if os.path.isfile(os.path.join(skill_dir, "scripts", f)))
            has_refs = os.path.isdir(os.path.join(skill_dir, "references")) and \
                len([f for f in os.listdir(os.path.join(skill_dir, "references")) if not f.startswith(".")]) > 0
            skills.append({
                "name": fm.get("name", entry),
                "description": fm.get("description", "—")[:60],
                "version": fm.get("version", "—"),
                "scripts": "✅" if has_scripts else "—",
                "refs": "✅" if has_refs else "—",
            })

    print(f"| Name | Description | Version | Scripts | Refs |")
    print(f"|------|-------------|---------|---------|------|")
    for s in skills:
        print(f"| {s['name']} | {s['description']} | {s['version']} | {s['scripts']} | {s['refs']} |")
    print(f"\n**Total: {len(skills)} skills**")


def cmd_validate(args):
    """Validate a skill's structure."""
    skill_dir = os.path.join(SKILLS_DIR, args.name)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    errors = []

    if not os.path.exists(skill_dir):
        print(f"❌ Skill directory not found: {skill_dir}")
        sys.exit(1)

    if not os.path.exists(skill_md):
        errors.append("SKILL.md missing")
    else:
        with open(skill_md) as f:
            content = f.read()

        # Check frontmatter
        if not re.match(r"^---\s*\n", content):
            errors.append("Missing YAML frontmatter (---)")
        else:
            fm = parse_frontmatter(skill_md)
            if not fm.get("name"):
                errors.append("Frontmatter missing 'name'")
            if not fm.get("description"):
                errors.append("Frontmatter missing 'description'")
            if not fm.get("version"):
                errors.append("Frontmatter missing 'version'")

        # Check required sections
        required_sections = ["When to Use", "Procedure", "Verification"]
        for section in required_sections:
            if f"## {section}" not in content:
                errors.append(f"Missing section: ## {section}")

    if errors:
        print(f"❌ Validation failed for '{args.name}':")
        for e in errors:
            print(f"   - {e}")
        sys.exit(1)
    else:
        print(f"✅ Skill '{args.name}' is valid")


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Skill CRUD")
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Create a new skill from template")
    p_create.add_argument("--name", required=True, help="Skill name (kebab-case)")
    p_create.add_argument("--description", help="Skill description")

    # delete
    p_delete = sub.add_parser("delete", help="Archive a skill")
    p_delete.add_argument("--name", required=True, help="Skill name to archive")

    # list
    sub.add_parser("list", help="List all active skills")

    # validate
    p_validate = sub.add_parser("validate", help="Validate a skill's structure")
    p_validate.add_argument("--name", required=True, help="Skill name to validate")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "validate":
        cmd_validate(args)


if __name__ == "__main__":
    main()
