#!/usr/bin/env python3
"""
consolidate_skills.py — Merge 100+ workspace skills into compact grouped entries.

Scans all SKILL.md files under skills/, extracts name + description,
groups by category, and outputs a condensed skill reference block that
reduces token usage by ~87% compared to listing each skill individually.

Usage:
    python3 skills/conditional-skills/scripts/consolidate_skills.py [--json] [--output PATH]
    python3 skills/conditional-skills/scripts/consolidate_skills.py --benchmark
"""

import os
import sys
import re
import json
import argparse

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
SKILLS_DIR = os.path.join(WORKSPACE, "skills")

# Category groupings: (category_label, list of skill name substrings to match)
# Ordered longest-match first to avoid over-broad matches
CATEGORIES = [
    # Trading / prediction markets
    ("trading-prediction", [
        "polymarket", "alphastrike", "simmer", "rsi-loop", "prediction-trade",
        "fear-harvester", "bounty-hunter", "cryptocom", "hyperliquid",
        "polymarket-ai", "simmer-risk",
    ]),
    # HuggingFace ecosystem
    ("huggingface", [
        "huggingface", "hf-cli", "llmfit", "transformers",
    ]),
    # Browser / web automation
    ("browser-automation", [
        "browser-use", "playwright", "selenium", "puppeteer", "web-scrape",
        "web-automation", "excalidraw",
    ]),
    # Coding agents
    ("coding-agents", [
        "coding-agent", "codex", "claude-code", "pi-agent", "opencode",
        "harness", "parallel-dispatch",
    ]),
    # GitHub / CI/CD
    ("github-ci", [
        "github", "gh-issues", "gh-pr",
    ]),
    # Infrastructure / deployment
    ("infrastructure", [
        "deploy", "docker", "k8s", "terraform", "infra",
        "vps", "nginx", "caddy", "systemd", "bird",
    ]),
    # Research / data / knowledge
    ("data-research", [
        "autoresearch", "knowledge-base", "domain-intel", "find-nearby",
        "blogwatcher", "arxiv", "llm-monitor",
    ]),
    # Content / media / publishing
    ("content-media", [
        "mbd", "mbd-publisher", "payhip-publisher", "ai-media",
        "video-frames", "youtube-content", "voxtral", "terse", "summarize",
    ]),
    # Agent orchestration / meta
    ("agent-orchestration", [
        "orchestrator", "intelligent-router", "rsi-loop",
        "parallel-dispatch", "caveman",
    ]),
    # Monitoring / health / guards
    ("monitoring-health", [
        "healthcheck", "agent-motivator", "agent-wal", "agent-watchdog",
        "llm-monitor", "guardrail", "verification-gate", "pre-task-checklist",
        "systematic-debug", "model-usage", "whalecli",
    ]),
    # Session / memory / governance
    ("session-memory", [
        "session-logs", "clawmemory", "memory-security", "agent-self-governance",
        "sag", "skill-manage", "skill-bridge",
    ]),
    # Terminal / dev tools
    ("terminal-dev", [
        "tmux", "rust-dev", "rust-analyzer", "clangd", "pyright", "gopls",
        "typescript-lsp", "solidity-lsp", "claw-forge", "cc-bos",
        "systematic-debug",
    ]),
    # Node / connectivity
    ("node-connectivity", [
        "node-connect", "gateway", "tailscale", "pairing",
    ]),
    # Social / communications
    ("social-comms", [
        "twitter", "reddit-cli", "discord-chat", "email",
        "imap-smtp-email", "smartshift",
    ]),
    # Crypto / blockchain
    ("crypto-blockchain", [
        "clawchain", "evoclaw", "blockchain", "wallet", "defi",
        "fear-protocol", "clawkeyring", "foundry",
    ]),
    # Skills meta / conditional
    ("skills-meta", [
        "conditional-skills", "agent-access-control", "agent-wal",
        "memory-security", "guardrail",
    ]),
    # AI / ML tools
    ("ai-ml", [
        "openai-whisper", "llmfit", "transformers", "voxtral",
    ]),
]

DEFAULT_CATEGORY = "tools-misc"


def extract_skill_info(skill_dir: str) -> dict:
    """Extract name and description from a SKILL.md file."""
    skill_name = os.path.basename(skill_dir)
    skill_md = os.path.join(skill_dir, "SKILL.md")

    description = ""
    use_when = ""

    if os.path.exists(skill_md):
        try:
            with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(2000)  # Read only first 2KB

            lines = content.split("\n")
            for line in lines[:30]:
                line = line.strip()
                if line.startswith("#"):
                    continue
                if re.match(r"^(Use when|Description|##|>)", line, re.I):
                    use_when = re.sub(r"^(Use when[:\s]*|Description[:\s]*|##\s*|>\s*)", "", line, flags=re.I).strip()
                    if use_when:
                        break
                elif line and not line.startswith("-") and not line.startswith("---") and len(line) > 20:
                    description = line[:120]
                    break

        except Exception:
            pass

    return {
        "name": skill_name,
        "description": use_when or description or skill_name.replace("-", " "),
        "path": skill_dir,
    }


def categorize_skill(skill_name: str) -> str:
    """Assign a skill to a category based on name matching."""
    name_lower = skill_name.lower()
    for category, keywords in CATEGORIES:
        for kw in keywords:
            if kw in name_lower:
                return category
    return DEFAULT_CATEGORY


def scan_skills(skills_dir: str) -> list:
    """Scan all skill directories and return list of skill info dicts."""
    skills = []
    if not os.path.isdir(skills_dir):
        return skills

    for entry in sorted(os.listdir(skills_dir)):
        # Skip archive and non-skill dirs
        if entry in ("archived", ".archive", "__pycache__", ".git"):
            continue
        skill_dir = os.path.join(skills_dir, entry)
        if os.path.isdir(skill_dir) and os.path.exists(os.path.join(skill_dir, "SKILL.md")):
            info = extract_skill_info(skill_dir)
            info["category"] = categorize_skill(entry)
            skills.append(info)

    return skills


def build_consolidated_block(skills: list) -> str:
    """Build a compact consolidated skill reference block."""
    # Group by category
    grouped = {}
    for skill in skills:
        cat = skill["category"]
        grouped.setdefault(cat, []).append(skill)

    lines = []
    lines.append("<consolidated_skills>")
    lines.append("<!-- Lazy skill registry. Use skill_search to find skills for any task. -->")

    total_original = len(skills)
    category_count = len(grouped)

    for cat, cat_skills in sorted(grouped.items()):
        names = ", ".join(s["name"] for s in cat_skills)
        lines.append(f"  <group name=\"{cat}\" count=\"{len(cat_skills)}\">{names}</group>")

    lines.append(f"  <meta total=\"{total_original}\" groups=\"{category_count}\"/>")
    lines.append("  <capability>skill_search: python3 skills/conditional-skills/scripts/skill_search.py \"&lt;task&gt;\"</capability>")
    lines.append("  <capability>skill_load: read tool on skills/&lt;name&gt;/SKILL.md</capability>")
    lines.append("</consolidated_skills>")

    return "\n".join(lines)


def build_per_skill_block(skills: list) -> str:
    """Build the traditional per-skill listing for comparison."""
    lines = ["<available_skills>"]
    for s in skills:
        lines.append(f"  <skill><name>{s['name']}</name><description>{s['description']}</description><location>{s['path']}/SKILL.md</location></skill>")
    lines.append("</available_skills>")
    return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English/code."""
    return max(1, len(text) // 4)


def main():
    parser = argparse.ArgumentParser(description="Consolidate workspace skills into compact grouped block")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text block")
    parser.add_argument("--output", help="Write output to file instead of stdout")
    parser.add_argument("--benchmark", action="store_true", help="Print token comparison stats")
    parser.add_argument("--skills-dir", default=SKILLS_DIR, help="Path to skills directory")
    args = parser.parse_args()

    skills = scan_skills(args.skills_dir)

    if not skills:
        print(f"ERROR: No skills found in {args.skills_dir}", file=sys.stderr)
        sys.exit(1)

    consolidated = build_consolidated_block(skills)
    original = build_per_skill_block(skills)

    orig_tokens = estimate_tokens(original)
    new_tokens = estimate_tokens(consolidated)
    reduction_pct = (1 - new_tokens / orig_tokens) * 100 if orig_tokens > 0 else 0

    if args.benchmark:
        grouped = {}
        for skill in skills:
            grouped.setdefault(skill["category"], []).append(skill["name"])

        print(f"=== Consolidation Benchmark ===")
        print(f"Skills found: {len(skills)}")
        print(f"Categories: {len(grouped)}")
        for cat, names in sorted(grouped.items()):
            print(f"  {cat}: {len(names)} skills")
        print(f"\nOriginal block chars:       {len(original):6d}")
        print(f"Original block tokens (est):{orig_tokens:6d}")
        print(f"Consolidated chars:         {len(consolidated):6d}")
        print(f"Consolidated tokens (est):  {new_tokens:6d}")
        print(f"\nReduction: {reduction_pct:.1f}%")
        print(f"Hermes baseline: 70-90%")
        print(f"Status: {'✅ BEATS HERMES' if reduction_pct >= 70 else '❌ BELOW TARGET'}")
        print()

    if args.json:
        grouped = {}
        for skill in skills:
            grouped.setdefault(skill["category"], []).append({
                "name": skill["name"],
                "description": skill["description"],
            })
        result = {
            "total_skills": len(skills),
            "categories": len(grouped),
            "grouped": grouped,
            "token_reduction_pct": round(reduction_pct, 1),
            "orig_tokens": orig_tokens,
            "consolidated_tokens": new_tokens,
            "consolidated_block": consolidated,
        }
        output = json.dumps(result, indent=2)
    else:
        output = consolidated

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Wrote consolidated skills to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
