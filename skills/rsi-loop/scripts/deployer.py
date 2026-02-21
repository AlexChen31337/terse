#!/usr/bin/env python3
"""
RSI Loop - Deployer
Deploys approved improvement proposals into the agent's live configuration.
Each action_type has a dedicated handler.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Gene Registry integration (Phase 2 of RSI loop)
try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from gene_registry import get_gene, update_gene_stats
    _GENE_REGISTRY_AVAILABLE = True
except ImportError:
    _GENE_REGISTRY_AVAILABLE = False

SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
PROPOSALS_DIR = DATA_DIR / "proposals"
WORKSPACE = Path.home() / "clawd"

def load_proposal(proposal_id: str) -> dict:
    path = PROPOSALS_DIR / f"{proposal_id}.json"
    if not path.exists():
        matches = list(PROPOSALS_DIR.glob(f"{proposal_id}*.json"))
        if not matches:
            raise FileNotFoundError(f"Proposal '{proposal_id}' not found")
        path = matches[0]
    with open(path) as f:
        return json.load(f)

def save_proposal(p: dict):
    path = PROPOSALS_DIR / f"{p['id']}.json"
    with open(path, "w") as f:
        json.dump(p, f, indent=2)

def mark_deployed(p: dict, notes: str = ""):
    p["status"] = "deployed"
    p["deployed_at"] = datetime.now(timezone.utc).isoformat()
    if notes:
        p["deployment_notes"] = notes
    save_proposal(p)

def deploy_create_skill(p: dict, dry_run: bool = False) -> str:
    """Scaffold a new skill directory using skill-creator's init script."""
    task_type = p["pattern"]["task_type"]
    skill_name = task_type.replace("_", "-")
    init_script = Path("/home/bowen/.local/share/fnm/node-versions/v22.22.0/installation/lib/node_modules/openclaw/skills/skill-creator/scripts/init_skill.py")

    if not init_script.exists():
        return f"ERROR: skill-creator init script not found at {init_script}"

    target = WORKSPACE / "skills" / skill_name
    if target.exists():
        return f"SKIP: Skill '{skill_name}' already exists at {target}"

    cmd = [
        sys.executable, str(init_script),
        skill_name,
        "--path", str(WORKSPACE / "skills"),
        "--resources", "scripts,references"
    ]

    if dry_run:
        return f"DRY RUN: Would run: {' '.join(cmd)}"

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return f"Created skill scaffold at {target}\nNext: implement SKILL.md and scripts"
    else:
        return f"ERROR: {result.stderr}"

def deploy_update_soul(p: dict, dry_run: bool = False) -> str:
    """Append lesson learned to SOUL.md."""
    soul_path = WORKSPACE / "SOUL.md"
    if not soul_path.exists():
        return "ERROR: SOUL.md not found"

    lesson = p["implementation"].get("changes", "")
    issue = p["pattern"]["issue"]
    task = p["pattern"]["task_type"]

    # Extract the lesson from the proposal
    lesson_entry = (
        f"\n- **[auto-rsi]** [{task}] Avoid '{issue}': {p['description']}\n"
    )

    if dry_run:
        return f"DRY RUN: Would append to SOUL.md:\n{lesson_entry}"

    with open(soul_path, "a") as f:
        f.write(lesson_entry)

    return f"Appended lesson to SOUL.md: {lesson_entry.strip()}"

def deploy_fix_routing(p: dict, dry_run: bool = False) -> str:
    """Print routing fix instructions (requires manual application)."""
    config_path = WORKSPACE / "skills" / "intelligent-router" / "config.json"
    if not config_path.exists():
        return "ERROR: intelligent-router config.json not found"

    changes = p["implementation"].get("changes", "")
    if dry_run:
        return f"DRY RUN: Would update {config_path}\n{changes}"

    # For routing, we output the guidance for the agent to apply
    return (
        f"MANUAL ACTION REQUIRED - Update {config_path}:\n"
        f"{changes}\n\n"
        f"After updating, reload config with: openclaw gateway config.get"
    )

def deploy_update_memory(p: dict, dry_run: bool = False) -> str:
    """Append memory improvement to HEARTBEAT.md or tiered memory."""
    heartbeat_path = WORKSPACE / "HEARTBEAT.md"
    task = p["pattern"]["task_type"]
    changes = p["implementation"].get("changes", "")

    if dry_run:
        return f"DRY RUN: Would update HEARTBEAT.md for {task} memory continuity"

    return (
        f"MANUAL ACTION REQUIRED - Improve memory for '{task}':\n"
        f"{changes}\n\n"
        f"Suggested: Add '{task}' context retrieval to HEARTBEAT.md hydration section"
    )

def deploy_apply_gene(p: dict, dry_run: bool = False) -> str:
    """
    Deploy an apply_gene proposal by:
    1. Loading the referenced Gene from the registry
    2. Printing its implementation template
    3. Running each validation command and reporting pass/fail
    4. Updating gene stats (success_rate, times_applied, last_applied)
    5. Printing blast radius info
    """
    if not _GENE_REGISTRY_AVAILABLE:
        return "ERROR: gene_registry module not available — cannot apply gene proposal"

    gene_id = p.get("implementation", {}).get("gene_id")
    if not gene_id:
        return "ERROR: proposal.implementation.gene_id is missing"

    gene = get_gene(gene_id)
    if gene is None:
        return f"ERROR: Gene '{gene_id}' not found in registry"

    print(f"\n{'='*60}")
    print(f"Gene: {gene['gene_id']}")
    print(f"Title: {gene['meta']['title']}")
    print(f"Mutation type: {gene['mutation_type']}")
    print(f"Success rate: {gene['meta']['success_rate']:.0%} ({gene['meta']['times_applied']}x applied)")
    print(f"\nImplementation Template:")
    print(f"{'─'*60}")
    print(gene["implementation"].get("template", "(no template)"))
    print(f"{'─'*60}")

    # Blast radius
    blast = gene.get("blast_radius", {})
    print(f"\nBlast Radius: max {blast.get('max_files', '?')} files")
    allowed = blast.get("allowed_paths", [])
    if allowed:
        print("  Allowed paths:")
        for path in allowed:
            print(f"    • {path}")
    immutable = blast.get("immutable_paths", [])
    if immutable:
        print("  Immutable paths (require Bowen approval):")
        for path in immutable:
            print(f"    ⛔ {path}")

    if dry_run:
        print(f"\n[DRY RUN] Would run {len(gene['validation']['commands'])} validation command(s)")
        return f"DRY RUN: Gene '{gene_id}' template printed. Validation skipped."

    # Run validation commands
    print(f"\nValidation Commands:")
    validation = gene.get("validation", {})
    commands = validation.get("commands", [])
    all_passed = True
    for i, cmd in enumerate(commands, 1):
        print(f"\n  [{i}/{len(commands)}] $ {cmd}")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                print(f"  ✓ PASSED (exit 0)")
                if result.stdout.strip():
                    print(f"    stdout: {result.stdout.strip()[:300]}")
            else:
                all_passed = False
                print(f"  ✗ FAILED (exit {result.returncode})")
                if result.stderr.strip():
                    print(f"    stderr: {result.stderr.strip()[:300]}")
        except subprocess.TimeoutExpired:
            all_passed = False
            print(f"  ✗ TIMEOUT (>60s)")
        except Exception as e:
            all_passed = False
            print(f"  ✗ ERROR: {e}")

    # Update gene stats
    update_gene_stats(gene_id, success=all_passed)
    status_str = "SUCCESS" if all_passed else "FAILED"
    print(f"\n{'='*60}")
    print(f"Gene deployment: {status_str}")
    print(f"Stats updated: times_applied +1, success recorded: {all_passed}")

    return f"Gene '{gene_id}' applied — validation: {status_str}"


def deploy_proposal(proposal_id: str, dry_run: bool = False) -> str:
    p = load_proposal(proposal_id)

    if p["status"] not in ("approved", "draft"):
        return f"Proposal '{proposal_id}' status is '{p['status']}' - only 'approved' or 'draft' can be deployed"

    action_type = p["action_type"]
    print(f"\nDeploying: [{p['priority'].upper()}] {p['title']}")
    print(f"Action: {action_type}")
    print(f"Dry run: {dry_run}\n")

    handlers = {
        "create_skill": deploy_create_skill,
        "update_skill": deploy_create_skill,  # same handler, skill exists check skips it
        "update_soul": deploy_update_soul,
        "update_agents": deploy_update_soul,  # similar append pattern
        "fix_routing": deploy_fix_routing,
        "update_memory": deploy_update_memory,
        "add_cron": lambda p, dr: "add_cron: Use cron tool to implement: " + p["implementation"]["changes"],
        "apply_gene": deploy_apply_gene,
    }

    handler = handlers.get(action_type)
    if not handler:
        return f"No handler for action_type '{action_type}'"

    result = handler(p, dry_run)

    if not dry_run and "ERROR" not in result and "MANUAL" not in result:
        mark_deployed(p, notes=result[:200])

    return result

def main():
    parser = argparse.ArgumentParser(description="RSI Deployer - Deploy approved improvement proposals")
    sub = parser.add_subparsers(dest="cmd")

    # deploy command
    dep = sub.add_parser("deploy", help="Deploy a specific proposal")
    dep.add_argument("proposal_id", help="Proposal ID or prefix")
    dep.add_argument("--dry-run", action="store_true", help="Show what would happen without doing it")

    # deploy-all command
    dep_all = sub.add_parser("deploy-all", help="Deploy all approved proposals")
    dep_all.add_argument("--dry-run", action="store_true")

    # full-cycle command
    cycle = sub.add_parser("full-cycle", help="Run full RSI cycle: analyze -> synthesize -> auto-deploy low-effort items")
    cycle.add_argument("--days", type=int, default=7)
    cycle.add_argument("--auto-approve-below-mins", type=int, default=20,
                       help="Auto-approve proposals estimated under N minutes effort")
    cycle.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.cmd == "deploy":
        result = deploy_proposal(args.proposal_id, dry_run=args.dry_run)
        print(result)

    elif args.cmd == "deploy-all":
        from synthesizer import load_all_proposals
        approved = load_all_proposals("approved")
        if not approved:
            print("No approved proposals to deploy.")
            return
        for p in approved:
            print(f"\n--- {p['id']} ---")
            result = deploy_proposal(p["id"], dry_run=args.dry_run)
            print(result)

    elif args.cmd == "full-cycle":
        print("=== RSI Full Cycle ===\n")

        # Step 1: Analyze
        print("Step 1: Analyzing outcomes...")
        import analyzer
        data = analyzer.analyze(args.days)
        meta = data["meta"]
        patterns = data["patterns"]
        print(f"  {meta['outcomes']} outcomes | health score: {meta.get('health_score', 'N/A')} | {len(patterns)} patterns found")

        # Step 2: Synthesize
        print("\nStep 2: Synthesizing proposals...")
        import synthesizer
        proposals = synthesizer.generate_proposals_heuristic(patterns, max_proposals=5)
        saved = synthesizer.save_proposals(proposals)
        print(f"  Generated {len(proposals)} proposals")

        # Step 3: Auto-approve low-effort items
        print(f"\nStep 3: Auto-approving proposals < {args.auto_approve_below_mins}min effort...")
        auto_approved = []
        for p in proposals:
            effort = p["implementation"].get("estimated_effort", 999)
            if effort <= args.auto_approve_below_mins:
                p["status"] = "approved"
                synthesizer.save_proposals([p])
                auto_approved.append(p)
                print(f"  Auto-approved: {p['id']} ({effort}min)")

        # Step 4: Deploy auto-approved
        print(f"\nStep 4: Deploying {len(auto_approved)} auto-approved proposals...")
        for p in auto_approved:
            result = deploy_proposal(p["id"], dry_run=args.dry_run)
            print(f"  {p['id']}: {result[:100]}")

        # Summary
        remaining = [p for p in proposals if p not in auto_approved]
        print(f"\n=== Cycle Complete ===")
        print(f"  Patterns found: {len(patterns)}")
        print(f"  Proposals generated: {len(proposals)}")
        print(f"  Auto-deployed: {len(auto_approved)}")
        if remaining:
            print(f"  Awaiting review: {len(remaining)} proposals")
            print("  Review with: uv run python skills/rsi-loop/scripts/synthesizer.py list")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
