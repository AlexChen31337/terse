#!/usr/bin/env python3
"""
Communication Watchdog — scans email inbox (and future channels) for new messages,
classifies them, and surfaces only meaningful ones to Bowen via Telegram.

Classification tiers:
  QUARANTINE  — spam, bots, bounty scammers, automated noise → mark read, log
  ASK         — ambiguous relevance → ask Bowen
  ACTIONABLE  → surface to Bowen with summary + draft reply for approval

State: memory/comm-watchdog-state.json
  {
    "last_uid": 2154,           # highest UID processed
    "quarantined": [...],       # list of from addresses auto-quarantined
    "approved_senders": [...]   # senders Bowen has approved to get replies
  }
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path("/home/bowen/.openclaw/workspace")
STATE_FILE = WORKSPACE / "memory/comm-watchdog-state.json"
IMAP_SKILL = WORKSPACE / "skills/imap-smtp-email"

TELEGRAM_OWNER = "2069029798"

# ── Spam / noise patterns (auto-quarantine, no Bowen notification) ──────────
QUARANTINE_PATTERNS = [
    # Known bounty bots
    r"zhuzhushiwojia",
    # Generic bounty/crypto wallet spam
    r"USDT\s+TRC20",
    r"TMLkvEDrjvHEUbWYU",
    # GitHub automated bots
    r"stainless-app\[bot\]",
    r"dependabot\[bot\]",
    r"renovate\[bot\]",
    r"github-actions\[bot\]",
    # Mass recruiter spam patterns
    r"I came across your profile and thought",
    r"We have an exciting opportunity",
    r"我来认领",   # bounty claim spam
    r"立即开始！🦞",
]

# ── Known irrelevant senders (route to seen-but-quiet bucket) ───────────────
NOISE_SENDERS = {
    "notifications@github.com",  # handled separately — only surface if actionable
    "jobalerts-noreply@linkedin.com",  # LinkedIn job alerts — always noise
    "linkedin@e.linkedin.com",         # LinkedIn marketing emails
    "noreply@linkedin.com",            # LinkedIn notifications
}

# ── Relevance signals (if present → surface to Bowen) ───────────────────────
ACTIONABLE_SIGNALS = [
    # Real human correspondence
    r"auroracpa\.com\.au",      # Jack Gu / tax accountant
    r"anthropic\.com",           # Anthropic
    r"polkadot|substrate|web3",  # ecosystem
    r"clawchain|evoclaw|claw-forge",
    r"AlexChen31337",            # mentions of our GitHub identity
    r"bounty.*\$[5-9]\d{2}",    # bounties over $500
    r"bounty.*\$[1-9]\d{3}",    # bounties over $1k
    r"dn-institute|1712n",       # known bounty orgs we care about
    r"interview|offer|CTO|cofounder",
    r"grant|treasury|proposal",
    r"invoice|payment|paid",
    r"reply|response|following up",  # real human following up
]

# ── GitHub notification signals worth surfacing ──────────────────────────────
GITHUB_ACTIONABLE = [
    r"clawinfra",
    r"AlexChen31337",
    r"clawchain-sdk|evoclaw|claw-chain|claw-forge|fear-protocol|agent-tools|clawkeyring",
]


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_uid": 0, "quarantined": [], "approved_senders": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def run_imap(args, timeout=60):
    cmd = ["node", "scripts/imap.js"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=IMAP_SKILL, timeout=timeout)
    return result.stdout.strip()


def mark_read(uids):
    if not uids:
        return
    for uid in uids:
        try:
            run_imap(["mark-read", str(uid)])
        except Exception:
            pass


def matches_any(text, patterns):
    text_lower = text.lower()
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


def classify_email(email):
    """Returns ('quarantine'|'noise'|'ask'|'actionable', reason)"""
    sender = email.get("from", "")
    subject = email.get("subject", "")
    text = email.get("text", "") or email.get("snippet", "")
    combined = f"{sender} {subject} {text}"

    # Hard quarantine
    if matches_any(combined, QUARANTINE_PATTERNS):
        return "quarantine", f"spam/bot pattern in: {sender[:60]}"

    # GitHub notifications — only surface if about our repos
    if "notifications@github.com" in sender:
        if matches_any(combined, GITHUB_ACTIONABLE):
            return "actionable", f"GitHub notification about our repos"
        return "noise", "GitHub notification — unrelated repo"

    # Direct actionable signals
    if matches_any(combined, ACTIONABLE_SIGNALS):
        return "actionable", f"matches actionable signal"

    # Everything else: ask Bowen
    return "ask", f"unknown sender/content"


def send_telegram(message):
    """Send message to Bowen via OpenClaw sessions_send / Telegram."""
    # Use the message tool indirectly via a simple curl to OpenClaw internal API
    # We rely on the cron job running inside OpenClaw context which handles routing
    print(f"[TELEGRAM] {message}")
    # Write to a pending-notify file that the cron payload picks up
    notify_file = WORKSPACE / "memory/comm-watchdog-pending.json"
    pending = []
    if notify_file.exists():
        try:
            pending = json.loads(notify_file.read_text())
        except Exception:
            pass
    pending.append({"ts": datetime.now(timezone.utc).isoformat(), "message": message})
    notify_file.write_text(json.dumps(pending, indent=2))


def summarise_email(email):
    sender = email.get("from", "Unknown")
    subject = email.get("subject", "(no subject)")
    snippet = (email.get("text") or email.get("snippet") or "")[:300].replace("\n", " ")
    date = email.get("date", "")[:10]
    uid = email.get("uid", "?")
    return f"📧 [{date}] From: {sender[:60]}\nSubject: {subject[:80]}\nPreview: {snippet[:200]}...\nUID: {uid}"


def main():
    state = load_state()
    last_uid = state.get("last_uid", 0)

    print(f"[comm_watchdog] Starting. Last processed UID: {last_uid}", file=sys.stderr)

    # Fetch recent unread emails
    try:
        raw = run_imap(["check", "--limit", "30"], timeout=90)
        if not raw or raw.startswith("Error"):
            print(f"[comm_watchdog] IMAP fetch failed: {raw}", file=sys.stderr)
            return
        emails = json.loads(raw)
    except Exception as e:
        print(f"[comm_watchdog] Exception fetching email: {e}", file=sys.stderr)
        return

    if not emails:
        print("[comm_watchdog] No new emails.", file=sys.stderr)
        return

    new_max_uid = last_uid
    quarantine_uids = []
    noise_uids = []
    actionable = []
    ask_later = []

    for email in emails:
        uid = email.get("uid", 0)
        if uid <= last_uid:
            continue  # already processed

        new_max_uid = max(new_max_uid, uid)
        verdict, reason = classify_email(email)

        print(f"[comm_watchdog] UID {uid}: {verdict} — {reason}", file=sys.stderr)

        if verdict == "quarantine":
            quarantine_uids.append(uid)
        elif verdict == "noise":
            noise_uids.append(uid)
        elif verdict == "actionable":
            actionable.append(email)
        elif verdict == "ask":
            ask_later.append(email)

    # Mark quarantine + noise as read silently
    mark_read(quarantine_uids + noise_uids)

    if quarantine_uids:
        print(f"[comm_watchdog] Quarantined {len(quarantine_uids)} emails (spam/bots). Marked read.", file=sys.stderr)

    # Surface actionable items to Bowen
    if actionable:
        lines = [f"📬 **Inbox alert — {len(actionable)} actionable email(s):**\n"]
        for em in actionable:
            lines.append(summarise_email(em))
            lines.append("")
        lines.append("Reply with: `reply <uid> <your message>` OR `ignore <uid>` to dismiss.")
        send_telegram("\n".join(lines))

    # Surface ambiguous items as a batched ask
    if ask_later:
        lines = [f"📬 **{len(ask_later)} email(s) need your call (unclear relevance):**\n"]
        for em in ask_later[:5]:  # cap at 5 to avoid spam
            lines.append(summarise_email(em))
            lines.append("")
        lines.append("Reply: `reply <uid>` to engage, `ignore <uid>` to dismiss, `block <sender>` to quarantine.")
        send_telegram("\n".join(lines))

    # Update state
    state["last_uid"] = new_max_uid
    save_state(state)

    # Log summary
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "new_max_uid": new_max_uid,
        "quarantined": len(quarantine_uids),
        "noise": len(noise_uids),
        "actionable": len(actionable),
        "ask": len(ask_later),
    }
    log_file = WORKSPACE / "memory/comm-watchdog-log.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"[comm_watchdog] Done. quarantine={len(quarantine_uids)}, noise={len(noise_uids)}, actionable={len(actionable)}, ask={len(ask_later)}", file=sys.stderr)


if __name__ == "__main__":
    main()
