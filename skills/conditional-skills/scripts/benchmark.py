#!/usr/bin/env python3
"""
benchmark.py - Benchmark conditional skills vs baseline (all-always).

Simulates OpenClaw's evaluateRuntimeEligibility() for the current runtime,
counts skills before/after filtering, estimates token savings, and compares
against Hermes agent's claimed 70-90% reduction.

Usage:
    python3 skills/conditional-skills/scripts/benchmark.py
"""

import os
import re
import json
import shutil
import sys
from pathlib import Path

# ─── Token estimation ─────────────────────────────────────────────────────────
TOKENS_PER_SKILL_COMPACT = 15  # name + location only
TOKENS_PER_SKILL_FULL = 35    # name + location + description snippet


def probe_runtime():
    """Probe the current runtime environment."""
    import platform
    os_name = platform.system().lower()
    if os_name == "darwin":
        os_name = "darwin"
    elif os_name == "windows":
        os_name = "win32"
    else:
        os_name = "linux"

    bins_to_check = [
        "gopls", "pyright", "pylsp", "rust-analyzer", "solc", "solidity-ls",
        "typescript-language-server", "tsserver", "clangd",
        "ffmpeg", "chromium", "chromium-browser", "google-chrome",
        "tmux", "bird", "birdc", "git", "gh", "ssh", "docker",
        "cargo", "rustc", "node", "npm", "python3", "uv",
        "huggingface-cli", "clawhub", "whois", "dig",
    ]
    available = set()
    for b in bins_to_check:
        if shutil.which(b):
            available.add(b)

    env_to_check = [
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GH_TOKEN", "GITHUB_TOKEN",
        "HYPERLIQUID_KEY", "NOTION_API_KEY",
    ]
    env_set = set()
    for e in env_to_check:
        if os.environ.get(e):
            env_set.add(e)

    # Config keys known to be set from workspace config
    config_keys = {
        "channels.telegram",
        "channels.whatsapp",
    }

    return os_name, available, env_set, config_keys


def parse_openclaw_metadata(content: str):
    """
    Extract the openclaw metadata dict from SKILL.md frontmatter.

    Handles three formats:
      1. metadata: {"openclaw": {...}}  (inline JSON on one line)
      2. metadata.openclaw:\n  always: true\n  requires:\n    anyBins: [...]  (YAML block)
      3. metadata: |\n  {...}  (block scalar JSON)
    Returns the openclaw dict or None if not found.
    """
    if not (content.startswith("---\n") or content.startswith("---\r\n")):
        return None

    end = content.find("\n---", 3)
    if end == -1:
        return None
    frontmatter = content[3:end].strip()

    # Format 1: metadata: {...}  (inline JSON)
    m = re.search(r'^metadata\s*:\s*(\{.*\})\s*$', frontmatter, re.MULTILINE)
    if m:
        try:
            obj = json.loads(m.group(1))
            return obj.get("openclaw")
        except Exception:
            pass

    # Format 2: metadata.openclaw: (YAML block — our injected format)
    if "metadata.openclaw:" in frontmatter:
        result = {}
        am = re.search(r'always:\s*(true|false)', frontmatter)
        if am:
            result["always"] = am.group(1) == "true"

        req = {}
        for key in ["bins", "anyBins", "env", "anyEnv", "config", "os"]:
            m2 = re.search(rf'^\s+{key}:\s*\[([^\]]*)\]', frontmatter, re.MULTILINE)
            if m2:
                vals = [v.strip().strip('"\'') for v in m2.group(1).split(',') if v.strip()]
                req[key] = vals
        if req:
            result["requires"] = req

        if result:
            return result
        # metadata.openclaw: present but nothing parsed — means always (older format)
        return {"always": True}

    return None


def evaluate_skill(meta, os_name, available_bins, env_vars, config_keys):
    """
    Simulate OpenClaw's evaluateRuntimeEligibility().
    Returns (is_eligible: bool, reason: str).
    """
    if meta is None:
        return True, "no-metadata (legacy always)"

    # OS check
    os_filter = meta.get("os")
    if os_filter and os_name not in os_filter:
        return False, f"os mismatch: need {os_filter}"

    if meta.get("always"):
        return True, "always=true"

    req = meta.get("requires", {})
    if not req:
        return True, "empty requires (eligible)"

    # bins: ALL must be present
    for b in req.get("bins", []):
        if b not in available_bins:
            return False, f"missing bin: {b}"

    # anyBins: at least ONE
    any_bins = req.get("anyBins", [])
    if any_bins and not any(b in available_bins for b in any_bins):
        return False, f"no anyBins found {any_bins}"

    # env: ALL must be set
    for e in req.get("env", []):
        if e not in env_vars:
            return False, f"missing env: {e}"

    # anyEnv: at least ONE
    any_env = req.get("anyEnv", [])
    if any_env and not any(e in env_vars for e in any_env):
        return False, f"no anyEnv found {any_env}"

    # config: ALL must be set
    for c in req.get("config", []):
        if c not in config_keys:
            return False, f"missing config: {c}"

    return True, "all requires passed"


def collect_skills():
    """Collect all unique SKILL.md files from known skill directories."""
    skill_dirs = [
        "/media/DATA/.openclaw/workspace/skills",
        os.path.expanduser("~/.openclaw/skills"),
        os.path.expanduser("~/.agents/skills"),
    ]
    skills = []
    seen = set()
    for d in skill_dirs:
        p = Path(d)
        if not p.exists():
            continue
        for sm in sorted(p.rglob("SKILL.md")):
            # Skip archived
            if "archived" in sm.parts or ".archive" in sm.parts:
                continue
            key = sm.parent.name
            if key in seen:
                continue
            seen.add(key)
            skills.append(sm)
    return skills


def main():
    print("=" * 70)
    print("OpenClaw Conditional Skills Benchmark")
    print("=" * 70)

    os_name, avail_bins, env_vars, config_keys = probe_runtime()
    print(f"\nRuntime: OS={os_name}")
    print(f"Bins found: {', '.join(sorted(avail_bins))}")
    print(f"Env vars set: {', '.join(sorted(env_vars)) or 'none'}")
    print(f"Config keys: {', '.join(sorted(config_keys))}")

    skills = collect_skills()
    total = len(skills)

    eligible = []
    filtered_out = []
    no_metadata = []
    always_load = []
    cond_pass = []
    cond_fail = []

    for sk in skills:
        try:
            content = sk.read_text(errors="replace")
        except Exception:
            continue
        meta = parse_openclaw_metadata(content)
        ok, reason = evaluate_skill(meta, os_name, avail_bins, env_vars, config_keys)

        if meta is None:
            no_metadata.append((sk, reason))
        elif meta.get("always"):
            always_load.append((sk, reason))
        elif ok:
            cond_pass.append((sk, reason))
        else:
            cond_fail.append((sk, reason))

        if ok:
            eligible.append((sk, reason))
        else:
            filtered_out.append((sk, reason))

    n_eligible = len(eligible)
    n_filtered = len(filtered_out)
    n_no_meta = len(no_metadata)
    reduction_pct = (n_filtered / total * 100) if total > 0 else 0

    tok_base_c = total * TOKENS_PER_SKILL_COMPACT
    tok_after_c = n_eligible * TOKENS_PER_SKILL_COMPACT
    tok_base_f = total * TOKENS_PER_SKILL_FULL
    tok_after_f = n_eligible * TOKENS_PER_SKILL_FULL

    print(f"\n{'─' * 70}")
    print(f"SKILLS SUMMARY")
    print(f"{'─' * 70}")
    print(f"Total (deduplicated):          {total:>5}")
    print(f"  No metadata (always):        {n_no_meta:>5}  ({n_no_meta/total*100:.1f}%)")
    print(f"  always=true:                 {len(always_load):>5}  ({len(always_load)/total*100:.1f}%)")
    print(f"  Conditional (pass):          {len(cond_pass):>5}  ({len(cond_pass)/total*100:.1f}%)")
    print(f"  Conditional (filtered):      {len(cond_fail):>5}  ({len(cond_fail)/total*100:.1f}%)")
    print(f"\nELIGIBLE after filtering:      {n_eligible:>5}  ({n_eligible/total*100:.1f}%)")
    print(f"FILTERED OUT:                  {n_filtered:>5}  ({reduction_pct:.1f}% reduction)")

    print(f"\n{'─' * 70}")
    print(f"TOKEN ESTIMATES")
    print(f"{'─' * 70}")
    print(f"Compact (~{TOKENS_PER_SKILL_COMPACT} tok/skill):")
    print(f"  Baseline: {tok_base_c:,}  →  After: {tok_after_c:,}  (saved {tok_base_c-tok_after_c:,})")
    print(f"Full desc (~{TOKENS_PER_SKILL_FULL} tok/skill):")
    print(f"  Baseline: {tok_base_f:,}  →  After: {tok_after_f:,}  (saved {tok_base_f-tok_after_f:,})")

    print(f"\n{'─' * 70}")
    print(f"VS HERMES AGENT")
    print(f"{'─' * 70}")
    print(f"Hermes claimed:  70–90% reduction")
    print(f"This run:        {reduction_pct:.1f}% reduction")
    if reduction_pct >= 70:
        print("✅ Matches Hermes range")
    elif reduction_pct >= 40:
        print("⚠️  Significant but below Hermes — consider lazy content loading")
    else:
        print("❌ Below Hermes — more skills need conditional metadata or content lazy-loading")

    if filtered_out:
        print(f"\n{'─' * 70}")
        print(f"FILTERED OUT ({len(filtered_out)}):")
        print(f"{'─' * 70}")
        for sk, reason in sorted(filtered_out, key=lambda x: x[0].parent.name):
            print(f"  {sk.parent.name:<45} {reason}")

    if no_metadata:
        print(f"\n{'─' * 70}")
        print(f"NO METADATA ({len(no_metadata)}) — always injected (legacy):")
        print(f"{'─' * 70}")
        for sk, _ in sorted(no_metadata, key=lambda x: x[0].parent.name):
            print(f"  {sk.parent.name}")

    return {
        "total": total, "eligible": n_eligible, "filtered": n_filtered,
        "reduction_pct": round(reduction_pct, 1),
        "no_metadata": n_no_meta, "always_load": len(always_load),
        "cond_pass": len(cond_pass), "cond_fail": len(cond_fail),
        "tokens_compact_baseline": tok_base_c, "tokens_compact_after": tok_after_c,
        "tokens_full_baseline": tok_base_f, "tokens_full_after": tok_after_f,
    }


if __name__ == "__main__":
    main()
