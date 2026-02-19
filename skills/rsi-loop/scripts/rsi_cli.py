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

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
