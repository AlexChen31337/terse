#!/usr/bin/env python3
"""
RSI Loop - Synthesizer
Takes detected patterns and generates concrete improvement proposals.
Each proposal is a structured action plan with implementation details.
"""

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Gene Registry integration (Phase 2 of RSI loop)
try:
    from gene_registry import load_genes
    from selector import select_gene
    _GENE_REGISTRY_AVAILABLE = True
except ImportError:
    _GENE_REGISTRY_AVAILABLE = False

SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
PATTERNS_FILE = DATA_DIR / "patterns.json"
PROPOSALS_DIR = DATA_DIR / "proposals"

PROPOSAL_SCHEMA = {
    "id": "str",
    "created_at": "iso8601",
    "status": "draft|approved|rejected|deployed",
    "priority": "critical|high|medium|low",
    "pattern": {"category": "str", "task_type": "str", "issue": "str"},
    "title": "str",
    "description": "str",
    "action_type": "create_skill|update_skill|update_soul|update_agents|add_cron|fix_routing|update_memory",
    "implementation": {
        "target_file": "str",
        "changes": "str (detailed instructions or diff)",
        "estimated_effort": "minutes",
    },
    "validation_criteria": ["str"],
    "expected_improvement": "str",
}

def load_patterns() -> dict:
    if not PATTERNS_FILE.exists():
        raise FileNotFoundError(
            "No patterns.json found. Run analyzer.py first: "
            "uv run python skills/rsi-loop/scripts/analyzer.py"
        )
    with open(PATTERNS_FILE) as f:
        return json.load(f)

def generate_proposals_heuristic(patterns: list, max_proposals: int = 5) -> list:
    """
    Generate improvement proposals using heuristic rules (no LLM needed).
    For LLM-powered synthesis, use synthesize_with_llm().
    """
    proposals = []

    # Load genes once for the full batch (gene registry integration)
    _genes = []
    if _GENE_REGISTRY_AVAILABLE:
        try:
            _genes = load_genes()
        except Exception:
            _genes = []

    for p in patterns[:max_proposals]:
        proposal_id = str(uuid.uuid4())[:8]
        category = p["category"]
        task_type = p["task_type"]
        issue = p["issue"]

        # ── Gene Registry: check for a reusable fix pattern before generating ──
        if _genes:
            pattern_ctx = {
                "category": category,
                "issue": issue,
                "task_type": task_type,
            }
            matched_gene = select_gene(pattern_ctx, _genes)
            if matched_gene is not None:
                gene_proposal = {
                    "id": proposal_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "draft",
                    "priority": "high",
                    "pattern": {"category": category, "task_type": task_type, "issue": issue},
                    "title": f"[Gene] {matched_gene['meta']['title']}",
                    "description": (
                        f"Gene registry match: applying '{matched_gene['gene_id']}' "
                        f"(success_rate={matched_gene['meta']['success_rate']:.0%}) "
                        f"to address '{issue}' in '{task_type}' tasks."
                    ),
                    "action_type": "apply_gene",
                    "implementation": {
                        "gene_id": matched_gene["gene_id"],
                        "target_file": ", ".join(
                            matched_gene.get("blast_radius", {}).get("allowed_paths", ["(see gene)"])
                        ),
                        "changes": matched_gene["implementation"].get("template", ""),
                        "estimated_effort": matched_gene["implementation"].get("effort_minutes", 0),
                    },
                    "validation_criteria": matched_gene.get("validation", {}).get("success_criteria", []),
                    "expected_improvement": matched_gene.get("expected_improvement", ""),
                }
                proposals.append(gene_proposal)
                continue  # skip heuristic generation for this pattern
        # ── End Gene Registry check ──

        # Determine priority
        if p["impact_score"] > 0.3 or p["failure_rate"] > 0.7:
            priority = "critical"
        elif p["impact_score"] > 0.15 or p["failure_rate"] > 0.5:
            priority = "high"
        elif p["impact_score"] > 0.05:
            priority = "medium"
        else:
            priority = "low"

        # Category-specific proposals
        if category == "skill_gap":
            proposal = {
                "id": proposal_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "draft",
                "priority": priority,
                "pattern": {"category": category, "task_type": task_type, "issue": issue},
                "title": f"Create skill for '{task_type}' tasks",
                "description": (
                    f"Agent repeatedly struggles with '{task_type}' tasks ({p['frequency']}x, "
                    f"{p['failure_rate']:.0%} failure rate). A dedicated skill would provide "
                    f"procedural knowledge, scripts, and reference material."
                ),
                "action_type": "create_skill",
                "implementation": {
                    "target_file": f"skills/{task_type.replace('_', '-')}/",
                    "changes": (
                        f"1. Run: python3 skills/skill-creator/scripts/init_skill.py {task_type.replace('_', '-')} "
                        f"--path ~/clawd/skills --resources scripts,references\n"
                        f"2. Add scripts for common {task_type} workflows\n"
                        f"3. Add references for domain knowledge\n"
                        f"4. Write SKILL.md with clear triggering description"
                    ),
                    "estimated_effort": 60,
                },
                "validation_criteria": [
                    f"Success rate for '{task_type}' improves above 80%",
                    f"Average quality score improves above 3.5",
                    "No new skill_gap issues in next 7-day analysis",
                ],
                "expected_improvement": (
                    f"Estimated {p['failure_rate'] * 100:.0f}% → <20% failure rate for {task_type} tasks"
                ),
            }

        elif category == "model_routing":
            proposal = {
                "id": proposal_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "draft",
                "priority": priority,
                "pattern": {"category": category, "task_type": task_type, "issue": issue},
                "title": f"Fix model routing for '{task_type}' tasks",
                "description": (
                    f"'{issue}' occurs {p['frequency']}x during '{task_type}' tasks. "
                    f"Routing agent to appropriate model tier would reduce this."
                ),
                "action_type": "fix_routing",
                "implementation": {
                    "target_file": "skills/intelligent-router/config.json",
                    "changes": (
                        f"1. Review router config for '{task_type}' task classification\n"
                        f"2. If '{issue}' == 'rate_limit': reduce primary model tier, use cheaper fallback\n"
                        f"3. If '{issue}' == 'slow_response': prefer faster local models\n"
                        f"4. If '{issue}' == 'wrong_model_tier': adjust task complexity scoring\n"
                        f"5. Run: uv run python skills/intelligent-router/scripts/router.py classify '{task_type} task'"
                    ),
                    "estimated_effort": 20,
                },
                "validation_criteria": [
                    f"'{issue}' frequency drops by >50%",
                    "Response times improve",
                    "No cascading fallbacks in logs",
                ],
                "expected_improvement": f"Eliminate {p['frequency']}x rate limits/routing failures per week",
            }

        elif category == "memory_continuity":
            proposal = {
                "id": proposal_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "draft",
                "priority": priority,
                "pattern": {"category": category, "task_type": task_type, "issue": issue},
                "title": f"Improve memory continuity for '{task_type}'",
                "description": (
                    f"'{issue}' causes {p['failure_rate']:.0%} failure rate in '{task_type}' tasks. "
                    f"Tiered memory or session hydration improvements needed."
                ),
                "action_type": "update_memory",
                "implementation": {
                    "target_file": "HEARTBEAT.md / skills/tiered-memory/",
                    "changes": (
                        f"1. For context_loss: add critical {task_type} context to HEARTBEAT.md pre-fetch\n"
                        f"2. For memory_miss: improve tiered-memory tagging for {task_type}\n"
                        f"3. For compaction_lost_context: add WAL entry for {task_type} state\n"
                        f"4. Run: uv run python skills/tiered-memory/scripts/memory_cli.py store"
                    ),
                    "estimated_effort": 30,
                },
                "validation_criteria": [
                    "memory_miss frequency drops by >60%",
                    "context_loss incidents eliminated",
                    "Session hydration includes relevant context",
                ],
                "expected_improvement": f"Restore continuity for {task_type} tasks across session resets",
            }

        elif category == "behavior_pattern":
            proposal = {
                "id": proposal_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "draft",
                "priority": priority,
                "pattern": {"category": category, "task_type": task_type, "issue": issue},
                "title": f"Update behavioral rules for '{issue}' pattern",
                "description": (
                    f"Agent exhibits '{issue}' behavior {p['frequency']}x. "
                    f"A SOUL.md or AGENTS.md update would establish the correct pattern."
                ),
                "action_type": "update_soul",
                "implementation": {
                    "target_file": "SOUL.md or AGENTS.md",
                    "changes": (
                        f"1. For repeated_mistake: add to 'Lessons learned' in SOUL.md\n"
                        f"2. For over_confirmation: reinforce autonomy rules in SOUL.md\n"
                        f"3. For bad_routing: update routing rules in AGENTS.md\n"
                        f"4. Document the specific pattern and the correct behavior\n"
                        f"Notes from outcomes: {p['sample_notes']}"
                    ),
                    "estimated_effort": 15,
                },
                "validation_criteria": [
                    f"'{issue}' frequency drops to <1x per week",
                    "No new incidents of same pattern",
                ],
                "expected_improvement": f"Eliminate recurring '{issue}' behavior pattern",
            }

        else:
            proposal = {
                "id": proposal_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "draft",
                "priority": priority,
                "pattern": {"category": category, "task_type": task_type, "issue": issue},
                "title": f"Address '{issue}' in '{task_type}' tasks",
                "description": p["description"],
                "action_type": "update_agents",
                "implementation": {
                    "target_file": "AGENTS.md",
                    "changes": f"Investigate and document fix for: {p['description']}",
                    "estimated_effort": 30,
                },
                "validation_criteria": ["Issue frequency drops by >50%"],
                "expected_improvement": "Reduce failure rate and improve quality score",
            }

        proposals.append(proposal)

    return proposals

def save_proposals(proposals: list) -> list:
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    saved = []
    for p in proposals:
        path = PROPOSALS_DIR / f"{p['id']}.json"
        with open(path, "w") as f:
            json.dump(p, f, indent=2)
        saved.append(str(path))
    return saved

def load_all_proposals(status_filter: str = None) -> list:
    if not PROPOSALS_DIR.exists():
        return []
    proposals = []
    for f in sorted(PROPOSALS_DIR.glob("*.json")):
        try:
            with open(f) as fh:
                p = json.load(fh)
            if status_filter is None or p.get("status") == status_filter:
                proposals.append(p)
        except Exception:
            pass
    return proposals

def update_proposal_status(proposal_id: str, status: str) -> bool:
    path = PROPOSALS_DIR / f"{proposal_id}.json"
    if not path.exists():
        # try prefix match
        matches = list(PROPOSALS_DIR.glob(f"{proposal_id}*.json"))
        if not matches:
            return False
        path = matches[0]
    with open(path) as f:
        p = json.load(f)
    p["status"] = status
    p["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w") as f:
        json.dump(p, f, indent=2)
    return True

def main():
    parser = argparse.ArgumentParser(description="RSI Synthesizer - Generate improvement proposals")
    sub = parser.add_subparsers(dest="cmd")

    # generate command
    gen = sub.add_parser("generate", help="Generate proposals from latest patterns")
    gen.add_argument("--top", type=int, default=5, help="Max proposals to generate")

    # list command
    ls = sub.add_parser("list", help="List proposals")
    ls.add_argument("--status", choices=["draft", "approved", "rejected", "deployed"], default=None)

    # approve command
    approve = sub.add_parser("approve", help="Approve a proposal")
    approve.add_argument("proposal_id")

    # reject command
    reject = sub.add_parser("reject", help="Reject a proposal")
    reject.add_argument("proposal_id")

    # show command
    show = sub.add_parser("show", help="Show proposal details")
    show.add_argument("proposal_id")

    args = parser.parse_args()

    if args.cmd == "generate":
        data = load_patterns()
        patterns = data.get("patterns", [])
        if not patterns:
            print("No patterns found. Run: uv run python skills/rsi-loop/scripts/analyzer.py")
            sys.exit(1)

        proposals = generate_proposals_heuristic(patterns, args.top)
        saved = save_proposals(proposals)

        print(f"\nGenerated {len(proposals)} improvement proposals:\n")
        for p in proposals:
            print(f"  [{p['priority'].upper()}] {p['id']}: {p['title']}")
            print(f"         Action: {p['action_type']} | Effort: {p['implementation']['estimated_effort']}min")

        print(f"\nSaved to: {PROPOSALS_DIR}/")
        print("Review with: uv run python skills/rsi-loop/scripts/synthesizer.py list")
        print("Approve with: uv run python skills/rsi-loop/scripts/synthesizer.py approve <id>")

    elif args.cmd == "list":
        proposals = load_all_proposals(args.status)
        if not proposals:
            print("No proposals found.")
            return
        print(f"\n{'ID':12} {'PRIORITY':10} {'STATUS':10} {'TITLE'}")
        print("-" * 70)
        for p in proposals:
            print(f"{p['id']:12} {p['priority']:10} {p['status']:10} {p['title'][:45]}")

    elif args.cmd == "approve":
        ok = update_proposal_status(args.proposal_id, "approved")
        print("Approved." if ok else f"Proposal '{args.proposal_id}' not found.")

    elif args.cmd == "reject":
        ok = update_proposal_status(args.proposal_id, "rejected")
        print("Rejected." if ok else f"Proposal '{args.proposal_id}' not found.")

    elif args.cmd == "show":
        path = PROPOSALS_DIR / f"{args.proposal_id}.json"
        if not path.exists():
            matches = list(PROPOSALS_DIR.glob(f"{args.proposal_id}*.json"))
            if not matches:
                print(f"Proposal '{args.proposal_id}' not found.")
                sys.exit(1)
            path = matches[0]
        with open(path) as f:
            p = json.load(f)
        print(json.dumps(p, indent=2))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
