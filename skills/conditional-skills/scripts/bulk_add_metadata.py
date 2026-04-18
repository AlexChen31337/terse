#!/usr/bin/env python3
"""
bulk_add_metadata.py - Bulk-add conditional metadata to SKILL.md files.

Reads each SKILL.md, checks if it already has metadata.openclaw frontmatter,
and if not, adds appropriate metadata based on skill name and content.

Usage:
    uv run python skills/conditional-skills/scripts/bulk_add_metadata.py [--dry-run]
"""

import os
import re
import sys
import argparse
from pathlib import Path

# ─── Skill metadata rules ────────────────────────────────────────────────────
# Each entry: (pattern_substring, metadata_dict)
# Pattern matched against the skill directory name (basename).
# First match wins. Order matters — most specific first.

SKILL_RULES = [
    # ── Language Servers ──────────────────────────────────────────────────────
    ("gopls-lsp", {
        "requires": {"anyBins": ["gopls"]},
        "reason": "Go language server — only useful when gopls is installed",
    }),
    ("pyright-lsp", {
        "requires": {"anyBins": ["pyright", "pylsp"]},
        "reason": "Python language server — only useful when pyright/pylsp is installed",
    }),
    ("rust-analyzer-lsp", {
        "requires": {"anyBins": ["rust-analyzer"]},
        "reason": "Rust language server — only useful when rust-analyzer is installed",
    }),
    ("solidity-lsp", {
        "requires": {"anyBins": ["solc", "solidity-ls"]},
        "reason": "Solidity language server — only useful when solc/solidity-ls is installed",
    }),
    ("typescript-lsp", {
        "requires": {"anyBins": ["typescript-language-server", "tsserver"]},
        "reason": "TypeScript language server — only useful when tsserver is installed",
    }),
    ("clangd-lsp", {
        "requires": {"anyBins": ["clangd"]},
        "reason": "C/C++ language server — only useful when clangd is installed",
    }),
    ("rust-dev", {
        "requires": {"anyBins": ["cargo", "rustc"]},
        "reason": "Rust development skill — only useful when Rust toolchain is installed",
    }),

    # ── Media / external tools ────────────────────────────────────────────────
    ("video-frames", {
        "requires": {"bins": ["ffmpeg"]},
        "reason": "Video frame extraction requires ffmpeg",
    }),
    ("voxtral", {
        "requires": {"anyBins": ["ffmpeg"]},
        "reason": "Voxtral audio processing requires ffmpeg",
    }),
    ("ai-media", {
        "requires": {"anyBins": ["ffmpeg", "imagemagick", "convert"]},
        "reason": "AI media tools require ffmpeg or imagemagick",
    }),

    # ── Browser skills ────────────────────────────────────────────────────────
    ("browser-use", {
        "requires": {"anyBins": ["chromium-browser", "chromium", "google-chrome"]},
        "reason": "Browser automation requires a Chromium-based browser",
    }),
    ("autoresearch", {
        "requires": {"anyBins": ["chromium-browser", "chromium", "google-chrome"]},
        "reason": "Auto-research uses browser automation — requires a Chromium-based browser",
    }),
    ("excalidraw", {
        "requires": {"anyBins": ["chromium-browser", "chromium", "google-chrome"]},
        "reason": "Excalidraw uses browser — requires Chromium",
    }),

    # ── AI / API-keyed skills ─────────────────────────────────────────────────
    ("openai-whisper-api", {
        "requires": {"env": ["OPENAI_API_KEY"]},
        "reason": "OpenAI Whisper API requires OPENAI_API_KEY",
    }),

    # ── Trading / finance — always load for this workspace ────────────────────
    ("crypto-agent-trading", {
        "always": True,
        "reason": "Core trading skill for this workspace",
    }),
    ("hyperliquid", {
        "always": True,
        "reason": "Hyperliquid trading integration — always relevant for this workspace",
    }),
    ("alphastrike", {
        "always": True,
        "reason": "AlphaStrike trading strategy — always relevant for this workspace",
    }),
    ("cryptocom-trading-bot", {
        "always": True,
        "reason": "Crypto.com trading bot — always relevant for this workspace",
    }),
    ("polymarket", {
        "always": True,
        "reason": "Polymarket prediction market skill",
    }),
    ("polymarket-ai-divergence", {
        "always": True,
        "reason": "Polymarket AI divergence analysis",
    }),
    ("simmer", {
        "always": True,
        "reason": "Simmer trading/strategy skill",
    }),
    ("simmer-risk", {
        "always": True,
        "reason": "Simmer risk management skill",
    }),
    ("fear-harvester", {
        "always": True,
        "reason": "Fear & Greed harvester for market sentiment",
    }),
    ("prediction-trade-journal", {
        "always": True,
        "reason": "Prediction trade journal",
    }),
    ("rsi-loop", {
        "always": True,
        "reason": "RSI loop trading skill",
    }),
    ("whalecli", {
        "always": True,
        "reason": "WhaleCLI on-chain monitoring",
    }),

    # ── Messaging / channel ───────────────────────────────────────────────────
    ("discord-chat", {
        "requires": {"config": ["channels.discord"]},
        "reason": "Discord chat skill only needed when Discord channel is configured",
    }),
    ("twitter", {
        "always": True,
        "reason": "Twitter/X integration — active workspace channel",
    }),
    ("reddit-cli", {
        "always": True,
        "reason": "Reddit CLI — active workspace channel",
    }),
    ("imap-smtp-email", {
        "always": True,
        "reason": "Email integration — active workspace tool",
    }),
    ("email", {
        "always": True,
        "reason": "Email skill — active workspace tool",
    }),

    # ── Publishing skills ─────────────────────────────────────────────────────
    ("mbd-publisher", {
        "always": True,
        "reason": "MbD publisher — core publishing workflow",
    }),
    ("mbd", {
        "always": True,
        "reason": "MbD skill — core publishing workflow",
    }),
    ("payhip-publisher", {
        "always": True,
        "reason": "Payhip publisher — core publishing workflow",
    }),
    ("youtube-content", {
        "always": True,
        "reason": "YouTube content creation skill",
    }),

    # ── HuggingFace skills ────────────────────────────────────────────────────
    ("huggingface-community-evals", {
        "requires": {"anyBins": ["huggingface-cli", "huggingface_hub"]},
        "reason": "HuggingFace community evals requires HF CLI",
    }),
    ("huggingface-datasets", {
        "requires": {"anyBins": ["huggingface-cli", "python3"]},
        "reason": "HuggingFace datasets skill",
    }),
    ("huggingface-gradio", {
        "requires": {"anyBins": ["python3", "uv"]},
        "reason": "HuggingFace Gradio requires Python",
    }),
    ("huggingface-jobs", {
        "requires": {"anyBins": ["huggingface-cli"]},
        "reason": "HuggingFace Jobs requires HF CLI",
    }),
    ("huggingface-llm-trainer", {
        "requires": {"anyBins": ["python3", "uv"]},
        "reason": "HuggingFace LLM trainer requires Python",
    }),
    ("huggingface-paper-publisher", {
        "always": True,
        "reason": "HuggingFace paper publishing workflow",
    }),
    ("huggingface-papers", {
        "always": True,
        "reason": "HuggingFace papers monitoring",
    }),
    ("huggingface-trackio", {
        "requires": {"anyBins": ["python3", "uv"]},
        "reason": "HuggingFace TrackIO requires Python",
    }),
    ("huggingface-vision-trainer", {
        "requires": {"anyBins": ["python3", "uv"]},
        "reason": "HuggingFace vision trainer requires Python",
    }),
    ("hf-cli", {
        "requires": {"anyBins": ["huggingface-cli"]},
        "reason": "HuggingFace CLI skill requires huggingface-cli binary",
    }),
    ("llmfit", {
        "requires": {"anyBins": ["python3", "uv"]},
        "reason": "LLMFit training skill requires Python",
    }),
    ("transformers-js", {
        "requires": {"anyBins": ["node", "npm"]},
        "reason": "Transformers.js requires Node.js",
    }),

    # ── External CLI tools ────────────────────────────────────────────────────
    ("bird", {
        "requires": {"anyBins": ["bird", "birdc"]},
        "reason": "Bird routing daemon CLI — only useful when bird/birdc is installed",
    }),
    ("tmux", {
        "requires": {"bins": ["tmux"]},
        "reason": "tmux skill only useful when tmux is available",
    }),
    ("domain-intel", {
        "requires": {"anyBins": ["whois", "dig", "nslookup"]},
        "reason": "Domain intelligence requires whois/dig",
    }),
    ("find-nearby", {
        "always": True,
        "reason": "Find nearby locations — utility skill",
    }),
    ("smartshift-advisor", {
        "always": True,
        "reason": "SmartShift energy advisor skill",
    }),
    ("llm-monitor", {
        "requires": {"anyBins": ["python3", "uv"]},
        "reason": "LLM monitor requires Python",
    }),

    # ── Core always-load skills ───────────────────────────────────────────────
    ("conditional-skills", {
        "always": True,
        "reason": "Core plugin that manages conditional skill loading",
    }),
    ("agent-self-governance", {
        "always": True,
        "reason": "Core agent behavior governance — always needed",
    }),
    ("sag", {
        "always": True,
        "reason": "Core self-governance plugin for agent behavior",
    }),
    ("agent-motivator", {
        "always": True,
        "reason": "Core agent motivator patterns — always needed",
    }),
    ("agent-access-control", {
        "always": True,
        "reason": "Core access control — always needed",
    }),
    ("agent-wal", {
        "always": True,
        "reason": "Core write-ahead log system — always needed",
    }),
    ("clawchain", {
        "always": True,
        "reason": "Core ClawChain L1 blockchain integration",
    }),
    ("clawmemory", {
        "always": True,
        "reason": "Core memory management — always needed",
    }),
    ("claw-forge-cli", {
        "always": True,
        "reason": "Core ClawForge CLI tools",
    }),
    ("claude-code", {
        "always": True,
        "reason": "Core Claude Code CLI integration",
    }),
    ("knowledge-base", {
        "always": True,
        "reason": "Core knowledge base — always needed",
    }),
    ("model-usage", {
        "always": True,
        "reason": "Core model usage tracking — always needed",
    }),
    ("session-logs", {
        "always": True,
        "reason": "Core session logging — always needed",
    }),
    ("summarize", {
        "always": True,
        "reason": "Core summarization capability",
    }),
    ("blogwatcher", {
        "always": True,
        "reason": "Blog watching / content monitoring",
    }),
    ("bounty-hunter", {
        "always": True,
        "reason": "Bug bounty hunting workflows",
    }),
    ("clawchain-contributor", {
        "always": True,
        "reason": "ClawChain contributor guidelines — always needed",
    }),
    ("create-agent-skills", {
        "always": True,
        "reason": "Skill design patterns — always needed",
    }),
    ("skill-designer-agent-skills", {
        "always": True,
        "reason": "Skill design patterns — always needed",
    }),
    ("distilled-common-failure-modes", {
        "always": True,
        "reason": "Common failure modes reference — always needed for agent safety",
    }),
    ("intelligent-router", {
        "always": True,
        "reason": "Intelligent model router — core infrastructure",
    }),
    ("orchestrator", {
        "always": True,
        "reason": "Task orchestrator — core infrastructure",
    }),
    ("parallel-dispatch", {
        "always": True,
        "reason": "Parallel task dispatch — core infrastructure",
    }),
    ("harness", {
        "always": True,
        "reason": "Test harness skill — core infrastructure",
    }),
    ("skill-bridge", {
        "always": True,
        "reason": "Skill bridge — core infrastructure",
    }),
    ("skill-manage", {
        "always": True,
        "reason": "Skill management — core infrastructure",
    }),
    ("guardrail", {
        "always": True,
        "reason": "Safety guardrail skill — always needed",
    }),
    ("pre-task-checklist", {
        "always": True,
        "reason": "Pre-task checklist — always needed",
    }),
    ("verification-gate", {
        "always": True,
        "reason": "Verification gate — always needed",
    }),
    ("systematic-debug", {
        "always": True,
        "reason": "Systematic debugging guide — always useful",
    }),
    ("memory-security", {
        "always": True,
        "reason": "Memory security — always needed",
    }),
    ("cc-bos", {
        "always": True,
        "reason": "CC BOS skill — core workspace skill",
    }),
    ("caveman", {
        "always": True,
        "reason": "Caveman debugging skill",
    }),
    ("terse", {
        "always": True,
        "reason": "Terse communication mode",
    }),
]

# ── Distilled skills: browser-related keywords for conditional categorization ──
BROWSER_DISTILLED_KEYWORDS = [
    "browser profile", "browser automation", "web automation", "login state",
    "ssrf policy", "hostname-based navigation", "port conflict", "browser profile discovery",
    "verify login", "avoid hostname", "check for port",
]


def get_skill_name(skill_dir: Path) -> str:
    return skill_dir.name


def is_distilled(name: str) -> bool:
    return name.startswith("distilled-")


def get_distilled_metadata(skill_path: Path) -> dict:
    """Read distilled skill content, tag browser-related ones as conditional."""
    try:
        content = skill_path.read_text(errors="replace").lower()
        for kw in BROWSER_DISTILLED_KEYWORDS:
            if kw in content[:600]:
                return {
                    "requires": {"anyBins": ["chromium-browser", "chromium", "google-chrome"]},
                    "reason": "Distilled browser skill — only useful when a browser is available",
                }
    except Exception:
        pass
    return {
        "always": True,
        "reason": "Distilled agent behavior pattern — always needed",
    }


def find_rule(name: str) -> dict | None:
    """Return the first matching rule for a given skill name."""
    for pattern, meta in SKILL_RULES:
        if name == pattern or name.startswith(pattern) or pattern in name:
            return meta
    return None


def has_openclaw_metadata(content: str) -> bool:
    """Check if the frontmatter already contains metadata.openclaw or metadata: { openclaw..."""
    if not (content.startswith("---\n") or content.startswith("---\r\n")):
        return False
    end = content.find("\n---", 3)
    if end == -1:
        return False
    front = content[:end]
    return "openclaw" in front and "metadata" in front


def extract_frontmatter_end(content: str) -> int:
    """Return the index just after the closing --- of the frontmatter, or -1."""
    if not (content.startswith("---\n") or content.startswith("---\r\n")):
        return -1
    end = content.find("\n---", 3)
    if end == -1:
        return -1
    # Skip past the \n---
    return end + 4


def build_openclaw_meta_yaml(meta: dict) -> str:
    """Build the metadata: | JSON block string."""
    import json
    openclaw = {}
    if meta.get("always"):
        openclaw["always"] = True
    if "requires" in meta:
        openclaw["requires"] = meta["requires"]
    if "reason" in meta:
        openclaw["reason"] = meta["reason"]

    # Use the JSON inline format that OpenClaw uses
    json_str = json.dumps({"openclaw": openclaw}, separators=(',', ':'))
    return f'metadata: {json_str}'


def inject_metadata_into_frontmatter(content: str, meta: dict) -> str:
    """Inject metadata: { openclaw: ... } into existing frontmatter."""
    fm_end = extract_frontmatter_end(content)
    if fm_end == -1:
        # No frontmatter — prepend one
        fm = "---\n" + build_openclaw_meta_yaml(meta) + "\n---\n"
        return fm + content

    # Insert the metadata line before the closing ---
    close_pos = content.rfind("\n---", 3, fm_end)
    meta_line = "\n" + build_openclaw_meta_yaml(meta)
    return content[:close_pos] + meta_line + content[close_pos:]


def process_skill(skill_path: Path, dry_run: bool = False) -> str:
    """Process a single SKILL.md. Returns status string."""
    content = skill_path.read_text(errors="replace")

    if has_openclaw_metadata(content):
        return "skip (already has metadata)"

    name = skill_path.parent.name

    # Skip archived skills
    parts = skill_path.parts
    if "archived" in parts or ".archive" in parts:
        return "skip (archived)"

    # Determine metadata
    if is_distilled(name):
        meta = get_distilled_metadata(skill_path)
    else:
        meta = find_rule(name)
        if meta is None:
            # Default: always load unknown skills
            meta = {
                "always": True,
                "reason": f"Auto-classified as always-load (no specific rule for '{name}')",
            }

    new_content = inject_metadata_into_frontmatter(content, meta)

    if not dry_run:
        skill_path.write_text(new_content)

    cond = "always" if meta.get("always") else f"requires:{list(meta.get('requires', {}).keys())}"
    return f"updated ({cond})"


def main():
    parser = argparse.ArgumentParser(description="Bulk-add metadata.openclaw to SKILL.md files")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files, just report")
    args = parser.parse_args()

    skill_dirs = [
        "/media/DATA/.openclaw/workspace/skills",
        os.path.expanduser("~/.openclaw/skills"),
        os.path.expanduser("~/.agents/skills"),
    ]

    results = {"skip": 0, "updated": 0, "error": 0}
    updated_details = []

    for skill_dir in skill_dirs:
        p = Path(skill_dir)
        if not p.exists():
            continue
        for skill_md in sorted(p.rglob("SKILL.md")):
            try:
                status = process_skill(skill_md, dry_run=args.dry_run)
                if status.startswith("skip"):
                    results["skip"] += 1
                else:
                    results["updated"] += 1
                    updated_details.append(f"  [{skill_md.parent.name}] {status}")
                prefix = "DRY-RUN " if args.dry_run else ""
                print(f"{prefix}[{status}] {skill_md}")
            except Exception as e:
                results["error"] += 1
                print(f"[ERROR] {skill_md}: {e}", file=sys.stderr)

    print()
    print("=" * 60)
    print(f"Summary: {results['updated']} updated, {results['skip']} skipped, {results['error']} errors")
    if updated_details:
        print("\nUpdated skills:")
        print("\n".join(updated_details[:30]))
        if len(updated_details) > 30:
            print(f"  ... and {len(updated_details) - 30} more")


if __name__ == "__main__":
    main()
