#!/usr/bin/env python3
"""
LinkedIn Watchdog — scrapes Alex Chen's LinkedIn inbox and notifications
for new messages/tags, classifies them, writes pending notifications.

Uses browser-use (Playwright stealth) with cookie auth.
State: memory/linkedin-watchdog-state.json
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path("/home/bowen/.openclaw/workspace")
STATE_FILE = WORKSPACE / "memory/linkedin-watchdog-state.json"
PENDING_FILE = WORKSPACE / "memory/comm-watchdog-pending.json"

LINKEDIN_EMAIL = "alex.chen31337@gmail.com"
LINKEDIN_PASSWORD = "LinkedIn@AlexChen2026k!"
LINKEDIN_PROFILE = "https://www.linkedin.com/in/alexchen31337/"

# Spam/noise patterns — auto-dismiss
SPAM_PATTERNS = [
    "I came across your profile",
    "exciting opportunity",
    "We are hiring",
    "recruiter",
    "staffing",
    "talent acquisition",
    "job opening",
    "我来认领",
    "USDT",
    "crypto investment",
]

# Actionable signals — surface to Bowen
ACTIONABLE_SIGNALS = [
    "clawchain",
    "evoclaw",
    "claw-forge",
    "blockchain",
    "substrate",
    "polkadot",
    "grant",
    "treasury",
    "collaboration",
    "partnership",
    "co-founder",
    "cofounder",
    "investor",
    "investment",
    "auroracpa",
    "tax",
]


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen_message_ids": [], "last_check": None}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def add_pending_notification(message: str):
    pending = []
    if PENDING_FILE.exists():
        try:
            pending = json.loads(PENDING_FILE.read_text())
        except Exception:
            pass
    pending.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "message": message
    })
    PENDING_FILE.write_text(json.dumps(pending, indent=2))


def classify_message(sender: str, preview: str) -> str:
    text = f"{sender} {preview}".lower()
    for s in SPAM_PATTERNS:
        if s.lower() in text:
            return "spam"
    for s in ACTIONABLE_SIGNALS:
        if s.lower() in text:
            return "actionable"
    return "ask"


def make_llm():
    """Return a browser-use compatible LLM.

    Uses ChatOpenAI with Groq free tier (llama-3.3-70b-versatile) — no API key needed beyond Groq.
    Fallback: z.ai GLM-4.7 via OpenAI-compat.
    browser-use 0.1.x requires structured output; Groq supports it.
    """
    import os

    # Primary: Groq free tier (llama-3.3-70b-versatile) — fast and supports structured output
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        # Read from openclaw memory files if available
        import json
        try:
            cfg_path = os.path.expanduser("~/.openclaw/workspace/memory/api-keys.json")
            if os.path.exists(cfg_path):
                keys = json.loads(open(cfg_path).read())
                groq_key = keys.get("GROQ_API_KEY", "")
        except Exception:
            pass

    # Fallback: z.ai OpenAI-compat endpoint with known key
    z_ai_key = "5798a068323e4e06be0ffd76b36ede2c.wBE6lE4v0bULJVSz"
    z_ai_base = "https://api.z.ai/api/openai/v1"

    from langchain_openai import ChatOpenAI
    if groq_key:
        return ChatOpenAI(
            model="llama-3.3-70b-versatile",
            openai_api_key=groq_key,
            openai_api_base="https://api.groq.com/openai/v1",
            max_tokens=4096,
        )
    # Fallback: z.ai OpenAI-compat (GLM-4.7)
    return ChatOpenAI(
        model="glm-4.7",
        openai_api_key=z_ai_key,
        openai_api_base=z_ai_base,
        max_tokens=4096,
    )


async def check_linkedin():
    try:
        from browser_use import Agent
        # BrowserSession was added in 0.2.x; use Browser/BrowserConfig for 0.1.x
        try:
            from browser_use import BrowserSession
            _use_browser_session = True
        except ImportError:
            from browser_use import Browser, BrowserConfig
            _use_browser_session = False
    except ImportError as e:
        print(f"[linkedin_watchdog] browser-use import failed: {e}", file=sys.stderr)
        return []

    task = f"""
Go to LinkedIn and check messages for Alex Chen.

1. Navigate to https://www.linkedin.com/messaging/
2. Log in with email={LINKEDIN_EMAIL} if not already logged in. Password stored in sensitive_data.
3. For each conversation in the inbox, extract:
   - sender name
   - message preview (first ~100 chars)
   - timestamp
   - is_unread (true/false)
4. Also check https://www.linkedin.com/notifications/ for any mentions or tags
5. Return a JSON list of items: [{{"type": "message"|"notification", "sender": "...", "preview": "...", "timestamp": "...", "is_unread": true}}]
6. Return ONLY the JSON array, nothing else.
"""

    llm = make_llm()
    if _use_browser_session:
        session = BrowserSession(headless=True)
        agent = Agent(
            task=task,
            llm=llm,
            browser_session=session,
            sensitive_data={"linkedin_password": LINKEDIN_PASSWORD},
        )
    else:
        browser = Browser(config=BrowserConfig(headless=True))
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            sensitive_data={"linkedin_password": LINKEDIN_PASSWORD},
        )

    try:
        history = await agent.run(max_steps=20)
        result = history.final_result()
        if result:
            # Try to parse JSON from result
            import re
            match = re.search(r'\[.*\]', result, re.DOTALL)
            if match:
                return json.loads(match.group(0))
    except Exception as e:
        print(f"[linkedin_watchdog] Agent error: {e}", file=sys.stderr)

    return []


def main():
    state = load_state()
    seen_ids = set(state.get("seen_message_ids", []))

    print("[linkedin_watchdog] Starting LinkedIn check...", file=sys.stderr)

    items = asyncio.run(check_linkedin())

    if not items:
        print("[linkedin_watchdog] No items returned from LinkedIn.", file=sys.stderr)
        state["last_check"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        return

    actionable = []
    ask_later = []
    new_seen = []

    for item in items:
        if not item.get("is_unread", False):
            continue

        # Create a unique ID from sender + preview
        item_id = f"{item.get('sender','')}:{item.get('preview','')[:50]}"
        if item_id in seen_ids:
            continue

        new_seen.append(item_id)
        verdict = classify_message(item.get("sender", ""), item.get("preview", ""))

        if verdict == "spam":
            print(f"[linkedin_watchdog] Spam: {item.get('sender')}", file=sys.stderr)
            continue
        elif verdict == "actionable":
            actionable.append(item)
        else:
            ask_later.append(item)

    # Surface actionable
    if actionable:
        lines = [f"💼 **LinkedIn — {len(actionable)} actionable message(s):**\n"]
        for item in actionable:
            lines.append(f"From: {item.get('sender')}")
            lines.append(f"Preview: {item.get('preview', '')[:200]}")
            lines.append(f"Time: {item.get('timestamp', '')}")
            lines.append("")
        lines.append("Reply 'linkedin reply <sender> <message>' to respond with my approval.")
        add_pending_notification("\n".join(lines))

    # Surface ambiguous
    if ask_later:
        lines = [f"💼 **LinkedIn — {len(ask_later)} message(s) need your call:**\n"]
        for item in ask_later[:3]:
            lines.append(f"From: {item.get('sender')}")
            lines.append(f"Preview: {item.get('preview', '')[:200]}")
            lines.append("")
        lines.append("Reply: 'reply', 'ignore', or 'block' for each sender.")
        add_pending_notification("\n".join(lines))

    # Update state
    seen_ids.update(new_seen)
    state["seen_message_ids"] = list(seen_ids)[-500:]  # keep last 500
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    print(f"[linkedin_watchdog] Done. actionable={len(actionable)}, ask={len(ask_later)}, spam skipped.", file=sys.stderr)


if __name__ == "__main__":
    main()
