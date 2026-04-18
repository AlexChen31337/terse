# Third-Party Asset Guardrail System
**Status:** SPEC — not yet built  
**Author:** Alex Chen  
**Date:** 2026-02-22  
**Applies to:** EvoMap genes/capsules, ClawHub skills, npm/pip packages, any external code

---

## Problem

EvoClaw is about to connect to external marketplaces (EvoMap, ClawHub). Without guardrails, any fetched gene, capsule, or skill can:
- Read/exfiltrate private keys, Telegram tokens, HL credentials
- Modify agent behaviour (SOUL.md, cron jobs, config)
- Execute arbitrary shell commands
- Phone home to adversarial endpoints
- Introduce subtle logic bugs that only manifest under specific conditions

A single poisoned gene could compromise the entire stack. We build the quarantine layer **before** any external asset touches production.

---

## Architecture

```
External source (EvoMap / ClawHub / manual)
            │
            ▼
    ┌───────────────┐
    │  INTAKE GATE  │  Receive + hash + log. Nothing runs here.
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │   QUARANTINE  │  Isolated staging dir. Git-tracked. No prod access.
    │   STAGING     │  ~/.evoclaw/quarantine/<asset_id>/
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │  SHIELD SCAN  │  Static analysis. Pattern matching. Risk scoring.
    └───────┬───────┘
            │ score < 30 → AUTO REJECT
            │ score 30-70 → ALEX REVIEW
            │ score > 70 → SANDBOX TEST
            ▼
    ┌───────────────┐
    │  SANDBOX RUN  │  Docker/firejail. No network. No home dir.
    │  (score >70)  │  Functional test only. Observe behaviour.
    └───────┬───────┘
            │ test fails → REJECT
            │ test passes → ALEX REVIEW
            ▼
    ┌───────────────┐
    │  ALEX REVIEW  │  Summary card sent to Telegram. Approve/Reject.
    └───────┬───────┘
            │ reject → archived + blacklisted
            │ approve ↓
            ▼
    ┌───────────────┐
    │  MERGE        │  Copy to production. Changelog entry. Git commit.
    └───────────────┘
```

---

## Components

### 1. Intake Gate (`intake.py`)

Responsibilities:
- Accept asset from any source (EvoMap fetch, ClawHub install, manual drop)
- Compute SHA256 of asset content — this is the canonical `asset_id`
- Check against blacklist (`quarantine/blacklist.json`) — reject immediately if matched
- Check against already-approved whitelist — skip re-review if unchanged
- Write to `~/.evoclaw/quarantine/<asset_id>/` with metadata:
  ```
  quarantine/<asset_id>/
    raw/          # original files, untouched
    metadata.json # source, received_at, asset_type, sha256
    review.json   # scan_result, sandbox_result, decision, decided_at
  ```
- Log all intake events to `quarantine/intake.log`

### 2. Shield Scan (`shield_scan.py`)

Static analysis — no code executed. Produces a **risk score 0–100** (lower = safer).

**Pattern checks (each adds to risk score):**

| Pattern | Risk | Reason |
|---------|------|--------|
| `os.environ`, `getenv` | +15 | Credential exfiltration |
| `subprocess`, `os.system`, `exec(` | +20 | Shell execution |
| `open(` on paths outside skill dir | +15 | Filesystem access outside scope |
| `requests`, `httpx`, `urllib` to non-whitelisted domains | +20 | Data exfiltration |
| `socket`, `asyncio.open_connection` | +15 | Raw network access |
| `import pickle`, `eval(`, `exec(` | +25 | Arbitrary code execution |
| Hardcoded IPs / non-standard domains | +15 | C2 callback risk |
| Access to `~/.openclaw/`, `~/clawd/memory/` | +30 | Memory/credential theft |
| Access to `~/.ssh/`, `~/.config/` | +30 | Key theft |
| `git push`, `git commit` | +10 | Workspace modification |
| Modifies `SOUL.md`, `AGENTS.md`, `openclaw.json` | +40 | Identity/config hijack |

**Risk thresholds:**
- **0–29**: Low risk → proceed to sandbox
- **30–59**: Medium risk → Alex review required before sandbox
- **60–79**: High risk → Alex review + mandatory explanation
- **80–100**: Critical → auto-reject, blacklist source

Output: `review.json` with `scan_score`, `findings[]`, `recommendation`

### 3. Sandbox Runner (`sandbox_run.py`)

Executes asset in isolation. Two backends:

**Option A: Docker (preferred)**
```bash
docker run --rm \
  --network none \
  --memory 256m \
  --cpus 0.5 \
  --read-only \
  --tmpfs /tmp:size=64m \
  -v /path/to/asset:/skill:ro \
  evoclaw-sandbox:latest \
  python /skill/test_entrypoint.py
```

**Option B: firejail (fallback, no Docker)**
```bash
firejail --net=none --private --read-only \
  python test_entrypoint.py
```

Sandbox generates a standardised test: call the skill's main function with mock inputs, observe:
- Does it exit cleanly?
- Does it attempt network calls? (blocked → logged)
- Does it attempt filesystem writes outside /tmp? (blocked → logged)
- Does it produce expected output format?

Output: `sandbox_result` in `review.json` — `pass/fail` + behaviour log

### 4. Alex Review (`review_notifier.py`)

Sends a summary card to Telegram when human review is needed:

```
🔍 Asset Review Required

Type: ClawHub Skill / EvoMap Capsule
Name: fear-harvester-v2
Source: clawhub.com / evomap.ai
SHA256: abc123...

Shield Scan: ⚠️ Score 45/100
Findings:
  - Uses httpx (external HTTP calls)
  - Reads os.environ (env vars)
  - Allowed domains: api.hyperliquid.xyz ✓

Sandbox: ✅ Passed
  - No blocked network attempts
  - Output format correct

Approve? Reply:
  APPROVE abc123
  REJECT abc123
```

Alex listens for the reply and executes the decision.

### 5. Merge (`merge.py`)

On approval:
- Copy from `quarantine/<asset_id>/raw/` to production skill dir
- Write entry to `quarantine/approved.json` (whitelist for future re-installs)
- Append to `CHANGELOG.md` in the skill dir
- `git add + git commit` with message: `feat: install <name> v<ver> [guardrail-approved sha256:<id>]`
- Notify Alex: "✅ Merged: `<name>`. Ready to use."

On rejection:
- Add SHA256 to `quarantine/blacklist.json`
- Optionally blacklist the source domain/node_id
- Log reason

---

## Domain Allowlist

Network calls inside sandboxed skills are blocked by default. Approved domains (whitelist):

```json
{
  "allowed_domains": [
    "api.hyperliquid.xyz",
    "api.hyperliquid-testnet.xyz",
    "api.binance.com",
    "api.alternative.me",
    "api.simmer.markets",
    "polymarket.com",
    "clam.polymarket.com",
    "integrate.api.nvidia.com",
    "api.z.ai",
    "api.deepseek.com",
    "testnet.clawchain.win",
    "clawhub.com"
  ]
}
```

Anything outside this list = flagged in scan + blocked in sandbox.

---

## Skill Installation Policy

### ClawHub skills (`openclaw skill install <name>`)
- Always goes through quarantine first
- `openclaw skill install` should be intercepted and rerouted to `intake.py`
- **Exception**: skills already in `approved.json` with matching SHA256 can skip review

### EvoMap genes/capsules
- Read-only fetch (observe market): ✅ no guardrail needed (data only)
- Apply fetched capsule to codebase: ❌ must go through full quarantine
- Auto-apply from loop: **NEVER** — always human-in-the-loop for code changes

### Manual drops
- Any `.py`, `.js`, `.sh`, `.toml` dropped into `~/.evoclaw/skills/` manually
- Watched by a file watcher cron → auto-intake on detection

---

## File Structure

```
~/.evoclaw/
  quarantine/
    blacklist.json        # SHA256s of rejected assets
    approved.json         # SHA256s of approved assets (skip re-review)
    intake.log            # all intake events
    <asset_id>/
      raw/                # original files
      metadata.json
      review.json

~/clawd/
  skills/
    guardrail/
      SKILL.md
      scripts/
        intake.py
        shield_scan.py
        sandbox_run.py
        review_notifier.py
        merge.py
        guardrail_cli.py  # CLI: guardrail install <path|url>
      config/
        domain_allowlist.json
        scan_rules.json
      tests/
        test_shield_scan.py
        test_intake.py
        test_merge.py
```

---

## Implementation Phases

### Phase 1 — Core pipeline (build this first)
- `intake.py` + `shield_scan.py` + `review_notifier.py` + `merge.py`
- Telegram approval/reject flow
- Basic static analysis (pattern matching)
- Manual CLI: `guardrail install <path>`
- Tests: ≥90% coverage

### Phase 2 — Sandbox
- Docker sandbox runner
- firejail fallback
- Network interception logging
- Domain allowlist enforcement

### Phase 3 — Automation hooks
- Intercept `openclaw skill install`
- EvoMap fetch → auto-intake (data fetch ok, capsule-apply goes to quarantine)
- File watcher for manual drops to `~/.evoclaw/skills/`

### Phase 4 — EvoMap integration (only after Phase 2 complete)
- Register EvoClaw Hub on EvoMap
- Implement GEP-A2A publisher (selective genes only)
- Bounty task claiming with Shield vetting

---

## Non-Negotiables

1. **No auto-apply of external code. Ever.** Human approval required for any code that touches production.
2. **SHA256 is the source of truth.** Same hash = same asset = same approval status.
3. **Quarantine is append-only.** Never delete from `quarantine/`. Audit trail is permanent.
4. **Blacklist is global.** Rejected SHA256 is rejected everywhere, forever (unless manually overridden by Bowen).
5. **Phase 2 (sandbox) must complete before EvoMap registration.**

---

*Next step: Build Phase 1. Spawn Builder subagent with this spec.*
