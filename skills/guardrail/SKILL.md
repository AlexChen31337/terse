---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'guardrail')"
---

# Guardrail Skill

Third-party asset vetting pipeline. Every external gene, capsule, or skill goes through this before touching production.

## Pipeline

```
intake → shield scan → telegram review → merge/reject
```

## Usage

```bash
cd ~/clawd/skills/guardrail

# Full pipeline (quarantine → scan → Telegram card → wait for reply → merge)
uv run python scripts/guardrail_cli.py install /path/to/skill_dir

# With metadata
uv run python scripts/guardrail_cli.py install /path/to/skill --name "my-skill" --type "ClawHub skill" --url "https://clawhub.com/my-skill"

# Non-blocking (notify and exit; approve/reject manually later)
uv run python scripts/guardrail_cli.py install /path/to/skill --no-wait

# Check status
uv run python scripts/guardrail_cli.py status <asset_id>

# List quarantine queue
uv run python scripts/guardrail_cli.py list

# Manual approve/reject
uv run python scripts/guardrail_cli.py approve <asset_id> --reason "reviewed, clean"
uv run python scripts/guardrail_cli.py reject  <asset_id> --reason "uses eval"
```

## Telegram Approval Flow

When an asset requires review, a card is sent to Bowen's Telegram with the scan score and findings. Reply with:

```
APPROVE <first-16-chars-of-sha256>
REJECT  <first-16-chars-of-sha256>
```

Then call `guardrail_cli.py approve/reject <full_asset_id>` to execute the decision.

## Risk Score Thresholds

| Score | Action |
|-------|--------|
| 0–29  | Auto-approve (proceed to sandbox in Phase 2) |
| 30–79 | Alex review required |
| 80+   | Auto-reject + blacklist source |

## Files

```
~/.evoclaw/quarantine/
  blacklist.json        # rejected SHA256s — permanent block
  approved.json         # approved SHA256s — skip re-review
  intake.log            # all intake events
  <sha256>/
    raw/                # original files, untouched
    metadata.json       # name, type, source_url, received_at
    review.json         # scan_score, findings, decision
```

## Tests

```bash
uv run pytest tests/ --cov=scripts --cov-report=term-missing
# 38 tests, 93% coverage
```

## Phase Roadmap

- **Phase 1** ✅ — intake + scan + Telegram review + merge (this skill)
- **Phase 2** 🔜 — Docker/firejail sandbox runner
- **Phase 3** 🔜 — Hook into `openclaw skill install`; EvoMap fetch auto-intake
- **Phase 4** 🔜 — EvoMap Hub registration (unlocks after Phase 2)
