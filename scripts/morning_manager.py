#!/usr/bin/env python3
"""
Morning Social/Correspondence Manager for Bowen.
Unified email + LinkedIn + GitHub triage and digest builder.

Modes:
  --mode email      Check email only
  --mode linkedin   Check LinkedIn only
  --mode github     Check GitHub mentions/PRs only
  --mode digest     Build morning digest from all channels
  --mode urgent     Quick scan for urgent items only
  --mode full       Run all channels + build digest (default)

State: memory/last_runs.json
Output: memory/morning-digest.md  (for digest mode)
        memory/urgent-items.json  (for urgent mode)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/media/DATA/.openclaw/workspace")
STATE_FILE = WORKSPACE / "memory/last_runs.json"
DIGEST_FILE = WORKSPACE / "memory/morning-digest.md"
URGENT_FILE = WORKSPACE / "memory/urgent-items.json"
COMM_PENDING = WORKSPACE / "memory/comm-watchdog-pending.json"
COMM_STATE = WORKSPACE / "memory/comm-watchdog-state.json"
LINKEDIN_STATE = WORKSPACE / "memory/linkedin-watchdog-state.json"

IMAP_SKILL = WORKSPACE / "skills/imap-smtp-email"

# ── Classification constants ────────────────────────────────────────────────

QUARANTINE_PATTERNS = [
    r"zhuzhushiwojia", r"USDT\s+TRC20", r"TMLkvEDrjvHEUbWYU",
    r"stainless-app\[bot\]", r"dependabot\[bot\]", r"renovate\[bot\]",
    r"github-actions\[bot\]",
    r"I came across your profile and thought",
    r"We have an exciting opportunity",
    r"我来认领", r"立即开始！🦞",
]

NOISE_SENDERS = {
    "jobalerts-noreply@linkedin.com", "linkedin@e.linkedin.com",
    "noreply@linkedin.com", "messages-noreply@linkedin.com",
    "updates-noreply@linkedin.com", "jobs-listings@linkedin.com",
    "no-reply@substack.com",
}

ACTIONABLE_SIGNALS = [
    r"auroracpa\.com\.au", r"anthropic\.com", r"polkadot|substrate|web3",
    r"clawchain|evoclaw|claw-forge", r"AlexChen31337",
    r"bounty.*\$[5-9]\d{2}", r"bounty.*\$[1-9]\d{3}",
    r"dn-institute|1712n", r"interview|offer|CTO|cofounder",
    r"grant|treasury|proposal", r"invoice|payment|paid",
    r"reply|response|following up",
    r"urgent|asap|immediate|critical|breaking",
]

URGENT_SIGNALS = [
    r"urgent|asap|immediate|critical|breaking|emergency",
    r"security.*breach|hack|compromised",
    r"invoice.*overdue|payment.*failed|chargeback",
    r"legal|lawsuit|cease.and.desist",
    r"server.*down|outage|incident",
]

GITHUB_ACTIONABLE = [
    r"clawinfra", r"AlexChen31337",
    r"clawchain-sdk|evoclaw|claw-chain|claw-forge|fear-protocol|agent-tools|clawkeyring",
]

AEST = timezone(timedelta(hours=11))


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {
        "last_email_uid": 0, "last_linkedin_check": None,
        "last_github_check": None, "last_morning_digest": None,
        "last_urgent_scan": None,
    }


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def matches_any(text, patterns):
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


def now_aest():
    return datetime.now(AEST)


def ts_iso():
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════
# EMAIL CHANNEL
# ═══════════════════════════════════════════════════════════════════════════

def run_imap(args, timeout=90):
    cmd = ["node", "scripts/imap.js"] + args
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=IMAP_SKILL, timeout=timeout
    )
    return result.stdout.strip()


def check_email(state, urgent_only=False):
    """Check email via IMAP skill. Returns list of classified items."""
    print("[morning_manager] Checking email...", file=sys.stderr)
    last_uid = state.get("last_email_uid", 0)
    items = []

    try:
        raw = run_imap(["check", "--limit", "30", "--unseen"], timeout=90)
        if not raw or raw.lower().startswith("error"):
            print(f"[morning_manager] IMAP fetch failed: {raw[:200]}", file=sys.stderr)
            return items
        emails = json.loads(raw)
    except Exception as e:
        print(f"[morning_manager] Email check error: {e}", file=sys.stderr)
        return items

    new_max_uid = last_uid
    for email in emails:
        uid = email.get("uid", 0)
        if uid <= last_uid:
            continue
        new_max_uid = max(new_max_uid, uid)

        sender = email.get("from", "")
        subject = email.get("subject", "")
        text = email.get("text", "") or email.get("snippet", "")
        combined = f"{sender} {subject} {text}"
        date = email.get("date", "")[:10]

        # Check urgent first
        is_urgent = matches_any(combined, URGENT_SIGNALS)

        # Classify
        if matches_any(combined, QUARANTINE_PATTERNS):
            verdict = "quarantine"
        elif any(ns in sender for ns in NOISE_SENDERS) and "notifications@github.com" not in sender:
            verdict = "noise"
        elif "notifications@github.com" in sender:
            if matches_any(combined, GITHUB_ACTIONABLE):
                verdict = "actionable"
            else:
                verdict = "noise"
        elif matches_any(combined, ACTIONABLE_SIGNALS):
            verdict = "actionable"
        else:
            verdict = "ask"

        if urgent_only and not is_urgent:
            continue

        items.append({
            "channel": "email",
            "uid": uid,
            "from": sender[:80],
            "subject": subject[:120],
            "preview": (text or "")[:300].replace("\n", " "),
            "date": date,
            "verdict": verdict,
            "urgent": is_urgent,
        })

    state["last_email_uid"] = new_max_uid
    print(f"[morning_manager] Email: {len(items)} items, max UID {new_max_uid}", file=sys.stderr)
    return items


# ═══════════════════════════════════════════════════════════════════════════
# GITHUB CHANNEL
# ═══════════════════════════════════════════════════════════════════════════

def check_github(state, urgent_only=False):
    """Check GitHub for mentions, assigned issues/PRs, and review requests."""
    print("[morning_manager] Checking GitHub...", file=sys.stderr)
    items = []

    # Check notifications for mentions
    try:
        result = subprocess.run(
            ["gh", "api", "/notifications", "--paginate", "-q",
             '.[] | select(.reason == "mention" or .reason == "assign" or .reason == "review_requested" or .reason == "author") | {subject: .subject.title, url: .subject.url, reason: .reason, repo: .repository.full_name, updated: .updated_at}'],
            capture_output=True, text=True, timeout=30
        )
        if result.stdout.strip():
            # Parse each line as JSON (gh -q outputs individual objects)
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    notif = json.loads(line)
                    repo = notif.get("repo", "")
                    subject = notif.get("subject", "")
                    url = notif.get("url", "")
                    reason = notif.get("reason", "")
                    updated = notif.get("updated", "")

                    is_urgent = any(kw in (subject + " " + repo).lower() for kw in
                                   ["urgent", "critical", "security", "broken", "down"])
                    if urgent_only and not is_urgent:
                        continue

                    items.append({
                        "channel": "github",
                        "subject": subject,
                        "url": url,
                        "repo": repo,
                        "reason": reason,
                        "updated": updated,
                        "verdict": "actionable",
                        "urgent": is_urgent,
                    })
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        print(f"[morning_manager] GitHub notifications error: {e}", file=sys.stderr)

    # Check specific repos for open issues/PRs assigned to us
    our_repos = [
        "clawinfra/claw-chain", "clawinfra/evoclaw",
        "clawinfra/clawchain-sdk", "clawinfra/agent-tools",
        "AlexChen31337/llm-knowledge-base",
    ]

    for repo in our_repos:
        try:
            # Open issues
            result = subprocess.run(
                ["gh", "issue", "list", "--repo", repo, "--state", "open",
                 "--limit", "5", "--json", "number,title,updatedAt,labels"],
                capture_output=True, text=True, timeout=15
            )
            if result.stdout.strip() and result.stdout.strip() != "[]":
                issues = json.loads(result.stdout.strip())
                for issue in issues:
                    labels = [l.get("name", "") for l in issue.get("labels", [])]
                    is_urgent = any(l in ["urgent", "critical", "P0", "bug"] for l in labels)
                    if urgent_only and not is_urgent:
                        continue
                    items.append({
                        "channel": "github",
                        "subject": f"#{issue['number']} {issue.get('title', '')}",
                        "url": f"https://github.com/{repo}/issues/{issue['number']}",
                        "repo": repo,
                        "reason": "open_issue",
                        "updated": issue.get("updatedAt", ""),
                        "verdict": "actionable" if is_urgent else "info",
                        "urgent": is_urgent,
                    })
        except Exception:
            pass

    state["last_github_check"] = ts_iso()
    print(f"[morning_manager] GitHub: {len(items)} items", file=sys.stderr)
    return items


# ═══════════════════════════════════════════════════════════════════════════
# LINKEDIN CHANNEL (lightweight check — no browser automation in cron)
# ═══════════════════════════════════════════════════════════════════════════

def check_linkedin_via_email(state, urgent_only=False):
    """
    Check LinkedIn activity via email notifications in Gmail.
    Full browser-based LinkedIn scraping is too heavy for frequent cron —
    that's done by linkedin_watchdog.py separately.
    This catches LinkedIn email notifications as a lightweight proxy.
    """
    print("[morning_manager] Checking LinkedIn via email notifications...", file=sys.stderr)
    items = []

    try:
        raw = run_imap(["search", "--from", "linkedin.com", "--recent", "24h", "--limit", "20"], timeout=60)
        if not raw or raw.lower().startswith("error"):
            print(f"[morning_manager] LinkedIn email search failed: {raw[:200]}", file=sys.stderr)
            return items
        emails = json.loads(raw) if raw else []
    except Exception as e:
        print(f"[morning_manager] LinkedIn email check error: {e}", file=sys.stderr)
        return items

    # Filter for actual message/comment notifications (not job alerts)
    message_patterns = [
        r"sent you a message", r"commented on your", r"mentioned you",
        r"replied to your", r"invited you to connect",
        r"endorsed you", r"shared your post",
    ]

    for email in emails:
        sender = email.get("from", "")
        subject = email.get("subject", "")
        text = email.get("text", "") or email.get("snippet", "")
        combined = f"{subject} {text}"

        # Only surface actual interaction notifications, not job alerts
        if not matches_any(combined, message_patterns):
            continue

        is_urgent = matches_any(combined, URGENT_SIGNALS)
        if urgent_only and not is_urgent:
            continue

        items.append({
            "channel": "linkedin",
            "from": sender[:80],
            "subject": subject[:120],
            "preview": (text or "")[:200].replace("\n", " "),
            "date": email.get("date", "")[:10],
            "verdict": "actionable",
            "urgent": is_urgent,
        })

    state["last_linkedin_check"] = ts_iso()
    print(f"[morning_manager] LinkedIn (email proxy): {len(items)} items", file=sys.stderr)
    return items


# ═══════════════════════════════════════════════════════════════════════════
# DIGEST BUILDER
# ═══════════════════════════════════════════════════════════════════════════

def build_digest(all_items):
    """Build a markdown digest from all classified items."""
    now = now_aest()
    date_str = now.strftime("%A, %B %d, %Y")

    email_actionable = [i for i in all_items if i["channel"] == "email" and i["verdict"] == "actionable"]
    email_ask = [i for i in all_items if i["channel"] == "email" and i["verdict"] == "ask"]
    github_items = [i for i in all_items if i["channel"] == "github"]
    linkedin_items = [i for i in all_items if i["channel"] == "linkedin"]

    urgent_items = [i for i in all_items if i.get("urgent")]

    lines = [f"# ☀️ Morning Digest — {date_str}\n"]

    # Urgent first
    if urgent_items:
        lines.append("## 🚨 Urgent / Needs Immediate Attention\n")
        for item in urgent_items:
            icon = {"email": "📧", "github": "🐙", "linkedin": "💼"}.get(item["channel"], "📌")
            lines.append(f"{icon} **[{item['channel'].upper()}]** {item.get('subject', item.get('from', 'Unknown'))}")
            if item.get("preview"):
                lines.append(f"   > {item['preview'][:200]}")
            if item.get("url"):
                lines.append(f"   🔗 {item['url']}")
            lines.append("")

    # Email
    if email_actionable:
        lines.append(f"## 📧 Email — {len(email_actionable)} Actionable\n")
        for item in email_actionable:
            lines.append(f"- **From:** {item['from']}")
            lines.append(f"  **Subject:** {item['subject']}")
            lines.append(f"  **Preview:** {item['preview'][:200]}")
            lines.append(f"  UID: {item.get('uid', '?')} | Date: {item.get('date', '')}")
            lines.append("")

    if email_ask:
        lines.append(f"## 📧 Email — {len(email_ask)} Need Your Decision\n")
        for item in email_ask[:5]:
            lines.append(f"- **From:** {item['from']}")
            lines.append(f"  **Subject:** {item['subject']}")
            lines.append(f"  **Preview:** {item['preview'][:200]}")
            lines.append("")

    # GitHub
    if github_items:
        lines.append(f"## 🐙 GitHub — {len(github_items)} Items\n")
        # Group by repo
        by_repo = {}
        for item in github_items:
            repo = item.get("repo", "other")
            by_repo.setdefault(repo, []).append(item)

        for repo, repo_items in sorted(by_repo.items()):
            lines.append(f"### {repo}")
            for item in repo_items:
                reason_icon = {"mention": "👤", "assign": "📋", "review_requested": "👀",
                              "author": "✍️", "open_issue": "📌"}.get(item.get("reason", ""), "•")
                lines.append(f"- {reason_icon} {item.get('subject', '(untitled)')} [{item.get('reason', '')}]")
                if item.get("url"):
                    lines.append(f"  🔗 {item['url']}")
            lines.append("")

    # LinkedIn
    if linkedin_items:
        lines.append(f"## 💼 LinkedIn — {len(linkedin_items)} Notifications\n")
        for item in linkedin_items:
            lines.append(f"- **{item.get('from', 'Unknown')}**: {item.get('subject', '')}")
            if item.get("preview"):
                lines.append(f"  > {item['preview'][:200]}")
            lines.append("")

    # Summary footer
    total = len(all_items)
    actionable_count = len([i for i in all_items if i["verdict"] == "actionable"])
    lines.append("---")
    lines.append(f"📊 Total: {total} items | Actionable: {actionable_count} | Urgent: {len(urgent_items)}")
    lines.append(f"Generated: {now.strftime('%H:%M %Z')}")

    digest_text = "\n".join(lines)
    DIGEST_FILE.write_text(digest_text)
    return digest_text


def build_telegram_digest(all_items):
    """Build a compact Telegram-friendly digest message."""
    urgent_items = [i for i in all_items if i.get("urgent")]
    email_actionable = [i for i in all_items if i["channel"] == "email" and i["verdict"] == "actionable"]
    github_items = [i for i in all_items if i["channel"] == "github" and i["verdict"] == "actionable"]
    linkedin_items = [i for i in all_items if i["channel"] == "linkedin"]

    now = now_aest()
    lines = [f"☀️ **Morning Digest — {now.strftime('%a %b %d')}**\n"]

    if urgent_items:
        lines.append("🚨 **URGENT:**")
        for item in urgent_items[:3]:
            icon = {"email": "📧", "github": "🐙", "linkedin": "💼"}.get(item["channel"], "📌")
            subj = item.get("subject", item.get("from", ""))
            lines.append(f"{icon} {subj[:80]}")

    if email_actionable:
        lines.append(f"\n📧 **Email:** {len(email_actionable)} actionable")
        for item in email_actionable[:5]:
            lines.append(f"  • {item.get('subject', '')[:70]}")

    if github_items:
        lines.append(f"\n🐙 **GitHub:** {len(github_items)} items")
        by_repo = {}
        for item in github_items:
            repo = item.get("repo", "")
            short_repo = repo.split("/")[-1] if "/" in repo else repo
            by_repo.setdefault(short_repo, 0)
            by_repo[short_repo] += 1
        for repo, count in sorted(by_repo.items(), key=lambda x: -x[1])[:5]:
            lines.append(f"  • {repo}: {count}")

    if linkedin_items:
        lines.append(f"\n💼 **LinkedIn:** {len(linkedin_items)} notifications")
        for item in linkedin_items[:3]:
            lines.append(f"  • {item.get('subject', '')[:70]}")

    total = len(all_items)
    lines.append(f"\n📊 Total: {total} items scanned")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# URGENT SCAN
# ═══════════════════════════════════════════════════════════════════════════

def check_urgent(state):
    """Quick scan for urgent items across all channels."""
    items = []
    items.extend(check_email(state, urgent_only=True))
    items.extend(check_github(state, urgent_only=True))
    # LinkedIn urgent via email notifications
    items.extend(check_linkedin_via_email(state, urgent_only=True))

    if items:
        URGENT_FILE.write_text(json.dumps(items, indent=2))
        print(f"[morning_manager] URGENT: {len(items)} urgent items found!", file=sys.stderr)
    else:
        # Clear previous urgents
        URGENT_FILE.write_text("[]")
        print("[morning_manager] No urgent items.", file=sys.stderr)

    state["last_urgent_scan"] = ts_iso()
    return items


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Morning Social/Correspondence Manager")
    parser.add_argument("--mode", default="full",
                       choices=["email", "linkedin", "github", "digest", "urgent", "full"],
                       help="Which mode to run")
    args = parser.parse_args()

    state = load_state()
    all_items = []

    if args.mode in ("email", "full"):
        email_items = check_email(state)
        all_items.extend(email_items)

    if args.mode in ("github", "full"):
        github_items = check_github(state)
        all_items.extend(github_items)

    if args.mode in ("linkedin", "full"):
        linkedin_items = check_linkedin_via_email(state)
        all_items.extend(linkedin_items)

    if args.mode == "urgent":
        urgent = check_urgent(state)
        # Print urgent items as JSON for the cron job to consume
        if urgent:
            print(json.dumps(urgent, indent=2))
        save_state(state)
        return

    if args.mode in ("digest", "full") and all_items:
        digest = build_digest(all_items)
        tg_digest = build_telegram_digest(all_items)
        state["last_morning_digest"] = ts_iso()

        # Print Telegram-friendly digest to stdout (cron picks this up)
        print("---TELEGRAM_DIGEST_START---")
        print(tg_digest)
        print("---TELEGRAM_DIGEST_END---")

        # Also print urgent items separately
        urgent = [i for i in all_items if i.get("urgent")]
        if urgent:
            print("---URGENT_ITEMS_START---")
            for item in urgent:
                icon = {"email": "📧", "github": "🐙", "linkedin": "💼"}.get(item["channel"], "📌")
                print(f"🚨 {icon} [{item['channel'].upper()}] {item.get('subject', item.get('from', ''))}")
            print("---URGENT_ITEMS_END---")

    # Log run
    log_entry = {
        "ts": ts_iso(),
        "mode": args.mode,
        "total_items": len(all_items),
        "actionable": len([i for i in all_items if i["verdict"] == "actionable"]),
        "urgent": len([i for i in all_items if i.get("urgent")]),
        "channels": list(set(i["channel"] for i in all_items)),
    }
    log_file = WORKSPACE / "memory/morning-manager-log.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    save_state(state)
    print(f"[morning_manager] Done. {len(all_items)} items processed.", file=sys.stderr)


if __name__ == "__main__":
    main()
