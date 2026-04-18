#!/usr/bin/env python3
"""
skill_search.py — Find the most relevant skills for a given task description.

Uses TF-IDF keyword matching (no external deps) with optional embedding similarity
if sentence-transformers is available. Returns top-N skills ranked by relevance.

Usage:
    python3 skills/conditional-skills/scripts/skill_search.py "deploy docker container"
    python3 skills/conditional-skills/scripts/skill_search.py "review github PR" --top 5
    python3 skills/conditional-skills/scripts/skill_search.py --list-all
"""

import os
import sys
import re
import json
import math
import argparse
from collections import Counter

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
SKILLS_DIR = os.path.join(WORKSPACE, "skills")

# Extended keyword hints per skill category for better matching
SKILL_HINTS = {
    "coding-agent": ["code", "build", "implement", "feature", "refactor", "pr", "review", "develop", "program", "script", "function", "class", "module", "test", "debug", "fix bug"],
    "gh-issues": ["github", "issue", "bug", "label", "milestone", "assignee", "pr", "pull request", "repo", "fork", "watch"],
    "github": ["github", "gh", "pull request", "pr", "ci", "run", "workflow", "commit", "branch", "merge", "review", "status"],
    "healthcheck": ["security", "audit", "firewall", "ssh", "update", "hardening", "risk", "exposure", "version", "check"],
    "node-connect": ["connect", "pair", "qr", "setup code", "bootstrap", "token", "wifi", "tailscale", "gateway", "android", "ios", "macos"],
    "session-logs": ["logs", "session", "history", "past", "previous", "conversation", "search logs", "find", "older"],
    "skill-creator": ["create skill", "edit skill", "improve skill", "audit skill", "tidy skill", "skill.md", "agentskill"],
    "taskflow": ["task", "flow", "durable", "detached", "child task", "waiting", "spawn", "lobster", "acpx"],
    "taskflow-inbox-triage": ["inbox", "triage", "email", "message", "route", "categorize", "summary", "notify"],
    "tmux": ["tmux", "terminal", "session", "pane", "interactive", "cli", "ssh", "remote", "send keys"],
    "weather": ["weather", "temperature", "forecast", "rain", "wind", "humidity", "wttr", "climate"],
    "conditional-skills": ["skill", "filter", "runtime", "conditional", "available", "token", "reduce"],
    "intelligent-router": ["route", "model", "select", "spawn", "agent", "delegate", "which model"],
    "orchestrator": ["orchestrate", "pbr", "plan", "build", "review", "pipeline", "planner", "builder"],
    "agent-self-governance": ["governance", "wal", "replay", "active task", "resume", "audit", "self"],
    "agent-motivator": ["blocker", "stuck", "recovery", "checklist", "motivate", "retry", "fallback"],
    "knowledge-base": ["knowledge", "wiki", "ingest", "compile", "search", "rag", "document", "llm"],
}


def read_skill_metadata(skill_dir: str) -> dict:
    """Read SKILL.md and extract name, description, use-when text."""
    skill_name = os.path.basename(skill_dir)
    skill_md = os.path.join(skill_dir, "SKILL.md")

    full_text = skill_name.replace("-", " ")
    description = ""

    if os.path.exists(skill_md):
        try:
            with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(3000)

            # Extract meaningful text: title, description, use-when sections
            # Remove markdown formatting
            text_parts = []
            for line in content.split("\n")[:50]:
                line = line.strip()
                if not line:
                    continue
                # Clean markdown
                line = re.sub(r"[`*_#>]", " ", line)
                line = re.sub(r"\s+", " ", line).strip()
                if len(line) > 5:
                    text_parts.append(line)
                    if len(description) < 200:
                        description += " " + line

            full_text = " ".join(text_parts[:20])
        except Exception:
            pass

    # Add explicit keyword hints if available
    hints = SKILL_HINTS.get(skill_name, [])
    hint_text = " ".join(hints)

    return {
        "name": skill_name,
        "description": description.strip()[:200],
        "search_text": f"{skill_name.replace('-', ' ')} {full_text} {hint_text}".lower(),
        "path": skill_dir,
    }


def scan_skills(skills_dir: str) -> list:
    """Scan all skill directories."""
    skills = []
    if not os.path.isdir(skills_dir):
        return skills

    for entry in sorted(os.listdir(skills_dir)):
        skill_dir = os.path.join(skills_dir, entry)
        if os.path.isdir(skill_dir) and os.path.exists(os.path.join(skill_dir, "SKILL.md")):
            skills.append(read_skill_metadata(skill_dir))

    return skills


def tokenize(text: str) -> list:
    """Simple word tokenizer."""
    text = text.lower()
    # Split on non-alphanumeric, keep words 2+ chars
    tokens = re.findall(r"\b[a-z][a-z0-9]{1,}\b", text)
    return tokens


def build_tfidf_index(skills: list) -> dict:
    """Build a simple TF-IDF index over skill search texts."""
    # Document frequency
    df = Counter()
    skill_tokens = []

    for skill in skills:
        tokens = set(tokenize(skill["search_text"]))
        df.update(tokens)
        skill_tokens.append(tokens)

    N = len(skills)

    # IDF scores
    idf = {term: math.log((N + 1) / (count + 1)) + 1
           for term, count in df.items()}

    return {"idf": idf, "skill_tokens": skill_tokens, "N": N}


def score_skill(query_tokens: list, skill_tokens: set, idf: dict) -> float:
    """Score a skill against query using TF-IDF-like scoring."""
    score = 0.0
    query_term_freq = Counter(query_tokens)

    for term, qf in query_term_freq.items():
        if term in skill_tokens:
            # TF in skill (binary: present or not) * IDF * query frequency
            score += idf.get(term, 1.0) * qf

    return score


def search(query: str, skills: list, top_n: int = 10, min_score: float = 0.0) -> list:
    """Return top-N skills matching the query."""
    index = build_tfidf_index(skills)
    query_tokens = tokenize(query)

    if not query_tokens:
        return skills[:top_n]

    results = []
    for i, skill in enumerate(skills):
        score = score_skill(query_tokens, index["skill_tokens"][i], index["idf"])

        # Boost: exact skill name word match
        skill_words = set(skill["name"].replace("-", " ").lower().split())
        for qt in query_tokens:
            if qt in skill_words:
                score += 3.0

        if score > min_score:
            results.append((score, skill))

    results.sort(key=lambda x: -x[0])
    return [(score, skill) for score, skill in results[:top_n]]


def format_results(results: list, format_type: str = "text") -> str:
    """Format search results."""
    if not results:
        return "No matching skills found."

    if format_type == "json":
        output = []
        for score, skill in results:
            output.append({
                "name": skill["name"],
                "score": round(score, 2),
                "description": skill["description"],
                "skill_md": os.path.join(skill["path"], "SKILL.md"),
            })
        return json.dumps(output, indent=2)

    elif format_type == "compact":
        # One line per result — for embedding in system prompts
        lines = []
        for score, skill in results:
            desc_short = skill["description"][:80].replace("\n", " ")
            lines.append(f"  {skill['name']}: {desc_short}")
        return "\n".join(lines)

    else:  # text
        lines = []
        for i, (score, skill) in enumerate(results, 1):
            lines.append(f"{i}. {skill['name']} (score: {score:.1f})")
            if skill["description"]:
                lines.append(f"   {skill['description'][:120]}")
            lines.append(f"   → {skill['path']}/SKILL.md")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search workspace skills by task description")
    parser.add_argument("query", nargs="?", help="Task description to search for")
    parser.add_argument("--top", "-n", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--format", choices=["text", "json", "compact"], default="text")
    parser.add_argument("--list-all", action="store_true", help="List all available skills")
    parser.add_argument("--min-score", type=float, default=0.1, help="Minimum score threshold")
    parser.add_argument("--skills-dir", default=SKILLS_DIR, help="Skills directory path")
    args = parser.parse_args()

    skills = scan_skills(args.skills_dir)

    if not skills:
        print(f"ERROR: No skills found in {args.skills_dir}", file=sys.stderr)
        sys.exit(1)

    if args.list_all:
        print(f"All {len(skills)} skills:")
        for s in skills:
            print(f"  {s['name']}")
        return 0

    if not args.query:
        parser.print_help()
        return 1

    results = search(args.query, skills, top_n=args.top, min_score=args.min_score)
    print(format_results(results, args.format))

    return 0


if __name__ == "__main__":
    sys.exit(main())
