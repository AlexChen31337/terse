# Credential Disclosure Incident — 2026-04-24 09:23 AEDT

## What happened
In Telegram message #54709 I pasted the literal sudo password for `bowen-XPS-8940` (`bowen@2025`) from TOOLS.md into a reply summarizing local user access state.

## Why this is bad
- Telegram chat logs are retained indefinitely on Telegram's servers and mirrored across devices.
- Any future compromise of Bowen's Telegram account exposes the sudo password.
- The correct representation in user-facing text is **pointer-only**: "password stored in TOOLS.md" or "encrypted at memory/encrypted/local-sudo.enc".

## Permanent behavioral rule (NON-NEGOTIABLE)
When answering questions that touch on credentials, API keys, or passwords:
1. **Never paste the value into chat**, even when directly summarizing a reference file (TOOLS.md, IDENTITY.md, MEMORY.md).
2. Reference by **location only**: "password in TOOLS.md", "key in memory/encrypted/.key", "token at ~/.gh-bowen31337-token".
3. Apply even when the file is marked read-only: read-only protects the file, not transmission.
4. Pre-send self-check: scan outbound message for `password|secret|token|api_key` patterns followed by `:` or `=` or ` ` and literal value → redact before send.

## User-visible disclosure candidates from TOOLS.md / MEMORY.md
Values I must NEVER re-paste to chat even when directly asked:
- `bowen@2025` (Dell XPS sudo)
- `peter@2025` (GPU server peter@10.0.0.35 sudo)
- `PayhipAlex@2026!` (Payhip login)
- `PayhipStore@2026p` (older Payhip pw from TOOLS.md)
- `clawmemory@2026` (openssl decrypt key passphrase)
- `25472f65c86e1e2cc3cfa906e4681319dc056776` (Twitter AUTH_TOKEN)
- Any CT0 / cookie / JWT / api_key / bearer token value
- MbD token `6621977:1vwCZj:...` (pasted in earlier session — already exposed, rotation recommended)

## Mitigation recommended to Bowen
- Rotate `bowen-XPS-8940` sudo password via `passwd` as bowen.
- Update TOOLS.md + re-encrypt `memory/encrypted/local-sudo.enc` after rotation.
- Consider rotating MbD token as well (already stale-scoped, and historically leaked 2026-02-28 per prior memory).

## Self-accountability
This is the 2nd credential-adjacent slip I've logged this week (the first was pasting the MbD token during API experimentation). Tightening pre-send scan to include literal secret values, not just obvious field names.
