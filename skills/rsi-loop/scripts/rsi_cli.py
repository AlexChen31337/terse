#!/usr/bin/env python3
"""
RSI Loop CLI - Unified interface for the Recursive Self-Improvement loop.
Run `uv run python skills/rsi-loop/scripts/rsi_cli.py --help` for usage.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent

def run_script(script: str, args: list) -> int:
    cmd = [sys.executable, str(SCRIPTS_DIR / script)] + args
    result = subprocess.run(cmd)
    return result.returncode

def cmd_gene(args):
    """Handle `gene` subcommands: list, show, validate, stats."""
    import subprocess as _sp
    sys.path.insert(0, str(SCRIPTS_DIR))
    from gene_registry import load_genes, get_gene
    from selector import select_gene

    sub = args.gene_cmd

    if sub == "list":
        genes = load_genes()
        if not genes:
            print("No genes in registry. Run: gene_registry.py")
            return
        print(f"\n{'GENE ID':<45} {'TYPE':<10} {'APPLIED':>7} {'SUCCESS':>8}")
        print("─" * 75)
        for g in genes:
            meta = g.get("meta", {})
            print(
                f"{g['gene_id']:<45} "
                f"{g.get('mutation_type', '?'):<10} "
                f"{meta.get('times_applied', 0):>7} "
                f"{meta.get('success_rate', 0.0):>7.0%}"
            )
        print(f"\n{len(genes)} gene(s) in registry.")

    elif sub == "show":
        gene = get_gene(args.gene_id)
        if gene is None:
            print(f"Gene '{args.gene_id}' not found.")
            sys.exit(1)
        print(json.dumps(gene, indent=2))

    elif sub == "validate":
        gene = get_gene(args.gene_id)
        if gene is None:
            print(f"Gene '{args.gene_id}' not found.")
            sys.exit(1)
        commands = gene.get("validation", {}).get("commands", [])
        if not commands:
            print("No validation commands defined for this gene.")
            return
        print(f"\nValidating gene: {gene['gene_id']}")
        print(f"Running {len(commands)} command(s)...\n")
        all_passed = True
        for i, cmd in enumerate(commands, 1):
            print(f"[{i}/{len(commands)}] $ {cmd}")
            result = _sp.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"  ✓ PASSED")
                if result.stdout.strip():
                    print(f"    {result.stdout.strip()[:200]}")
            else:
                all_passed = False
                print(f"  ✗ FAILED (exit {result.returncode})")
                if result.stderr.strip():
                    print(f"    {result.stderr.strip()[:200]}")
        print(f"\nResult: {'ALL PASSED ✓' if all_passed else 'SOME FAILED ✗'}")

    elif sub == "stats":
        genes = load_genes()
        if not genes:
            print("No genes in registry.")
            return
        # Group by mutation_type
        from collections import defaultdict
        groups = defaultdict(list)
        for g in genes:
            groups[g.get("mutation_type", "unknown")].append(g)
        print(f"\n{'MUTATION TYPE':<15} {'GENES':>6} {'TOTAL APPLIED':>14} {'AVG SUCCESS':>12}")
        print("─" * 52)
        for mtype, glist in sorted(groups.items()):
            total_applied = sum(g["meta"].get("times_applied", 0) for g in glist)
            applied_genes = [g for g in glist if g["meta"].get("times_applied", 0) > 0]
            if applied_genes:
                avg_success = sum(g["meta"].get("success_rate", 0) for g in applied_genes) / len(applied_genes)
            else:
                avg_success = 0.0
            print(
                f"{mtype:<15} {len(glist):>6} {total_applied:>14} {avg_success:>11.0%}"
            )

    else:
        print(f"Unknown gene subcommand: '{sub}'")
        print("Available: list, show <gene_id>, validate <gene_id>, stats")
        sys.exit(1)


def cmd_status(args):
    """Show overall RSI loop status."""
    from observer import stats_summary, load_outcomes
    from analyzer import load_patterns
    from synthesizer import load_all_proposals

    print("\n=== RSI Loop Status ===\n")

    # Outcomes
    stats = stats_summary(7)
    if stats["total"] == 0:
        print("Outcomes: No data yet. Start logging with: rsi_cli.py log ...")
    else:
        print(f"Outcomes (7d): {stats['total']} logged | "
              f"Success: {stats['success_rate']*100:.0f}% | "
              f"Avg quality: {stats['avg_quality']}/5")
        if stats.get("top_issues"):
            issues = ", ".join(f"{k}({v})" for k, v in stats["top_issues"][:3])
            print(f"  Top issues: {issues}")

    # Patterns
    data = load_patterns()
    if data:
        meta = data.get("meta", {})
        patterns = data.get("patterns", [])
        print(f"\nPatterns: {len(patterns)} detected | "
              f"Health score: {meta.get('health_score', 'N/A')} | "
              f"Analyzed: {meta.get('generated_at', 'unknown')[:10]}")
        for p in patterns[:3]:
            print(f"  [{p['impact_score']:.3f}] {p['description'][:70]}")
    else:
        print("\nPatterns: Not analyzed yet. Run: rsi_cli.py analyze")

    # Proposals
    all_proposals = load_all_proposals()
    draft = [p for p in all_proposals if p["status"] == "draft"]
    approved = [p for p in all_proposals if p["status"] == "approved"]
    deployed = [p for p in all_proposals if p["status"] == "deployed"]

    print(f"\nProposals: {len(draft)} draft | {len(approved)} approved | {len(deployed)} deployed")

    if approved:
        print("  Ready to deploy:")
        for p in approved:
            print(f"  - {p['id']}: {p['title'][:60]}")
            print(f"    Deploy: uv run python skills/rsi-loop/scripts/rsi_cli.py deploy {p['id']}")

    print("\nQuick actions:")
    print("  uv run python skills/rsi-loop/scripts/rsi_cli.py cycle   # Run full RSI cycle")
    print("  uv run python skills/rsi-loop/scripts/rsi_cli.py log     # Log a turn outcome")

def main():
    parser = argparse.ArgumentParser(
        description="RSI Loop - Recursive Self-Improvement for EvoClaw agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  status    Show RSI loop status
  log       Log a turn outcome (observer)
  analyze   Detect patterns from outcomes
  propose   Generate improvement proposals
  approve   Approve a proposal for deployment
  deploy    Deploy an approved proposal
  cycle     Run full RSI cycle (analyze + propose + deploy)

Examples:
  # Log a successful code generation task
  rsi_cli.py log --task code_generation --success true --quality 4 --model glm-4.7

  # Log a failed task with issue
  rsi_cli.py log --task code_debug --success false --quality 2 --issues skill_gap --notes "No skill for Rust debugging"

  # Run full improvement cycle
  rsi_cli.py cycle

  # Manual workflow
  rsi_cli.py analyze
  rsi_cli.py propose
  rsi_cli.py approve <id>
  rsi_cli.py deploy <id>
        """
    )
    sub = parser.add_subparsers(dest="cmd")

    # status
    sub.add_parser("status", help="Show RSI loop status")

    # log
    log_p = sub.add_parser("log", help="Log a turn outcome")
    log_p.add_argument("--task", required=True, help="Task type")
    log_p.add_argument("--success", required=True, choices=["true", "false"])
    log_p.add_argument("--quality", type=int, default=3)
    log_p.add_argument("--model", default="")
    log_p.add_argument("--duration-ms", type=int, default=0)
    log_p.add_argument("--issues", nargs="*", default=[])
    log_p.add_argument("--tags", nargs="*", default=[])
    log_p.add_argument("--notes", default="")
    log_p.add_argument("--agent-id", default="main")

    # analyze
    analyze_p = sub.add_parser("analyze", help="Detect patterns from logged outcomes")
    analyze_p.add_argument("--days", type=int, default=7)
    analyze_p.add_argument("--top", type=int, default=5)

    # propose
    propose_p = sub.add_parser("propose", help="Generate improvement proposals")
    propose_p.add_argument("--top", type=int, default=5)

    # approve
    approve_p = sub.add_parser("approve", help="Approve a proposal")
    approve_p.add_argument("proposal_id")

    # reject
    reject_p = sub.add_parser("reject", help="Reject a proposal")
    reject_p.add_argument("proposal_id")

    # deploy
    deploy_p = sub.add_parser("deploy", help="Deploy an approved proposal")
    deploy_p.add_argument("proposal_id")
    deploy_p.add_argument("--dry-run", action="store_true")

    # cycle
    cycle_p = sub.add_parser("cycle", help="Run full RSI cycle")
    cycle_p.add_argument("--days", type=int, default=7)
    cycle_p.add_argument("--auto-approve-below-mins", type=int, default=20)
    cycle_p.add_argument("--dry-run", action="store_true")

    # gene
    gene_p = sub.add_parser("gene", help="Manage the Gene registry")
    gene_sub = gene_p.add_subparsers(dest="gene_cmd")
    gene_sub.add_parser("list", help="List all genes")
    gene_show = gene_sub.add_parser("show", help="Show full gene JSON")
    gene_show.add_argument("gene_id")
    gene_val = gene_sub.add_parser("validate", help="Run validation commands for a gene")
    gene_val.add_argument("gene_id")
    gene_sub.add_parser("stats", help="Success rate per mutation type")

    args = parser.parse_args()

    if args.cmd == "status":
        sys.path.insert(0, str(SCRIPTS_DIR))
        from observer import stats_summary
        from analyzer import load_patterns
        from synthesizer import load_all_proposals
        cmd_status(args)

    elif args.cmd == "log":
        extra = []
        if args.issues:
            extra += ["--issues"] + args.issues
        if args.tags:
            extra += ["--tags"] + args.tags
        run_script("observer.py", [
            "log",
            "--task", args.task,
            "--success", args.success,
            "--quality", str(args.quality),
            "--model", args.model,
            "--duration-ms", str(args.duration_ms),
            "--notes", args.notes,
            "--agent-id", args.agent_id,
        ] + extra)

    elif args.cmd == "analyze":
        run_script("analyzer.py", ["--days", str(args.days), "--top", str(args.top)])

    elif args.cmd == "propose":
        run_script("synthesizer.py", ["generate", "--top", str(args.top)])

    elif args.cmd == "approve":
        run_script("synthesizer.py", ["approve", args.proposal_id])

    elif args.cmd == "reject":
        run_script("synthesizer.py", ["reject", args.proposal_id])

    elif args.cmd == "deploy":
        extra = ["--dry-run"] if args.dry_run else []
        run_script("deployer.py", ["deploy", args.proposal_id] + extra)

    elif args.cmd == "cycle":
        extra = []
        if args.dry_run:
            extra.append("--dry-run")
        run_script("deployer.py", [
            "full-cycle",
            "--days", str(args.days),
            "--auto-approve-below-mins", str(args.auto_approve_below_mins),
        ] + extra)

    elif args.cmd == "gene":
        sys.path.insert(0, str(SCRIPTS_DIR))
        if not args.gene_cmd:
            gene_p.print_help()
        else:
            cmd_gene(args)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
