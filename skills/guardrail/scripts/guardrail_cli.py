#!/usr/bin/env python3
"""
Guardrail CLI — vetting pipeline for third-party assets.

Commands:
    install <path>              Run full pipeline: intake → scan → notify → wait → merge/reject
    scan    <asset_id>          Re-run shield scan only
    status  <asset_id>          Show current review.json
    list                        List quarantine queue
    approve <asset_id> [--reason]   Manually approve
    reject  <asset_id> [--reason]   Manually reject
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).parent))

from intake import intake_asset, QUARANTINE_ROOT
from shield_scan import scan_asset
from review_notifier import notify_review, record_decision, wait_for_decision
from merge import merge_asset, reject_asset


@click.group()
def cli():
    """Guardrail — third-party asset vetting pipeline."""


@cli.command()
@click.argument("source")
@click.option("--name",   default=None, help="Human-readable asset name")
@click.option("--type",   "asset_type", default="manual", help="Asset type label")
@click.option("--url",    default=None, help="Source URL for metadata")
@click.option("--no-wait", is_flag=True, help="Don't wait for Telegram decision — just scan and notify")
def install(source, name, asset_type, url, no_wait):
    """Full pipeline: quarantine → scan → notify → merge."""
    click.echo(f"📥 Intake: {source}")
    result = intake_asset(source, asset_name=name, asset_type=asset_type, source_url=url)

    if result["status"] == "blacklisted":
        click.secho("🚫 BLOCKED — asset is blacklisted.", fg="red")
        sys.exit(1)

    if result["status"] == "already_approved":
        click.secho("✅ Already approved — skipping review.", fg="green")
        sys.exit(0)

    asset_id = result["asset_id"]
    click.echo(f"📦 Quarantined: {asset_id[:16]}...")

    click.echo("🔍 Running shield scan...")
    review = scan_asset(asset_id)
    score  = review["scan_score"]
    rec    = review["recommendation"]

    colour = {"approve": "green", "review": "yellow", "reject": "red"}.get(rec, "white")
    click.secho(f"   Score: {score}/100  →  {rec.upper()}", fg=colour)

    if rec == "reject":
        click.secho("🚫 Auto-rejected (score ≥ 80).", fg="red")
        reject_asset(asset_id, reason="auto-rejected by shield scan (score ≥ 80)")
        sys.exit(1)

    click.echo("📨 Sending Telegram review card...")
    notify_review(asset_id)

    if no_wait:
        click.echo("   --no-wait: exiting. Use `guardrail approve/reject <id>` later.")
        sys.exit(0)

    click.echo("⏳ Waiting for Telegram decision (up to 24h)...")
    decision = wait_for_decision(asset_id)

    if decision == "approved":
        click.echo("✅ Approved — merging...")
        merge_asset(asset_id)
        click.secho("Done.", fg="green")
    elif decision == "rejected":
        click.secho("🚫 Rejected.", fg="red")
        reject_asset(asset_id)
        sys.exit(1)
    else:
        click.secho("⏰ Timed out waiting for decision.", fg="yellow")
        sys.exit(1)


@cli.command()
@click.argument("asset_id")
def scan(asset_id):
    """Re-run shield scan on a quarantined asset."""
    review = scan_asset(asset_id)
    click.echo(json.dumps(review, indent=2))


@cli.command()
@click.argument("asset_id")
def status(asset_id):
    """Show review status for a quarantined asset."""
    dest = QUARANTINE_ROOT / asset_id
    if not dest.exists():
        click.secho(f"No quarantine entry for {asset_id}", fg="red")
        sys.exit(1)
    for fname in ("metadata.json", "review.json"):
        f = dest / fname
        if f.exists():
            click.echo(f"\n=== {fname} ===")
            click.echo(f.read_text())


@cli.command("list")
def list_queue():
    """List all assets in quarantine."""
    if not QUARANTINE_ROOT.exists():
        click.echo("Quarantine is empty.")
        return
    entries = [d for d in QUARANTINE_ROOT.iterdir() if d.is_dir()]
    if not entries:
        click.echo("Quarantine is empty.")
        return
    for entry in sorted(entries):
        meta_file   = entry / "metadata.json"
        review_file = entry / "review.json"
        name     = json.loads(meta_file.read_text()).get("name", "?") if meta_file.exists() else "?"
        decision = json.loads(review_file.read_text()).get("decision", "pending") if review_file.exists() else "not scanned"
        click.echo(f"  {entry.name[:16]}...  {name:<30} [{decision}]")


@cli.command()
@click.argument("asset_id")
@click.option("--reason", default="", help="Approval note")
def approve(asset_id, reason):
    """Manually approve a quarantined asset and merge it."""
    record_decision(asset_id, "approved", reason)
    merge_asset(asset_id)
    click.secho(f"✅ {asset_id[:16]}... approved and merged.", fg="green")


@cli.command()
@click.argument("asset_id")
@click.option("--reason", default="", help="Rejection reason")
def reject(asset_id, reason):
    """Manually reject and blacklist a quarantined asset."""
    record_decision(asset_id, "rejected", reason)
    reject_asset(asset_id, reason)
    click.secho(f"🚫 {asset_id[:16]}... rejected and blacklisted.", fg="red")


if __name__ == "__main__":
    cli()
