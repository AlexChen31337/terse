---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'mbd-publisher')"
---

# MbD Publisher Skill (面包多)

Publishes content to Bowen's MbD (面包多) account.

## ⚠️ Delegation Rule (NON-NEGOTIABLE)
This skill ALWAYS runs in a sub-agent via `sessions_spawn`. Never execute MbD publishing inline in the main session.

**Main agent:** spawn sub-agent → tell Bowen "publishing now" → done.
**Sub-agent:** write content → generate ZImage cover → call MbD API → report result.

```
sessions_spawn(task="Publish to MbD: [topic]", model="claude-code-plugin-1/claude-sonnet-4-6", mode="run")
```

Never block main chat with API calls, content generation, or image generation.

## Authentication
- Token: `memory/encrypted/mbd-token.enc`
- API base: `https://x.mbd.pub/api/`

## Publishing Rules
- **NEVER publish without explicit "publish to MbD" from Bowen.** Write → save → STOP.
- Every post MUST have a ZImage cover (768×1024)
- Negative prompt: `text, letters, numbers, words, characters, fonts, typography, logo, title, subtitle, caption, label, sign, writing, watermark`
- Topic rotation state: `memory/mbd-publisher-state.json`

## Publishing Flow
1. Decrypt MbD token from `memory/encrypted/mbd-token.enc`
2. Generate ZImage cover via ComfyUI (GPU server port 8188)
3. Draft content following topic rotation
4. POST to MbD API with cover image
5. Update `memory/mbd-publisher-state.json` with published entry
6. Report URL back to main agent
