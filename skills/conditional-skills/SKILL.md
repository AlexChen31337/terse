---
metadata.openclaw:
  always: true
  reason: "Core plugin that manages conditional skill loading"
---


# Conditional Skills — OpenClaw Native Activation

## How It Works

OpenClaw filters skills during session startup via `evaluateRuntimeEligibility()`. Skills without conditional metadata are always shown. Skills with a `metadata.openclaw` block in their YAML frontmatter are conditionally included/excluded based on runtime checks.

**This is built into OpenClaw core — no plugin needed.**

## Frontmatter Schema

Add a `metadata` block to your SKILL.md frontmatter:

```yaml
---
name: my-skill
description: "..."
version: 1.0.0
metadata: |
  {
    "openclaw": {
      "os": ["linux", "macos"],
      "always": false,
      "requires": {
        "bins": ["gh", "docker"],
        "anyBins": ["curl", "wget"],
        "env": ["GITHUB_TOKEN"],
        "config": ["channels.telegram"]
      }
    }
  }
---
```

## Fields Reference

| Field | Type | Behavior |
|-------|------|----------|
| `os` | `string[]` | Skill HIDDEN on non-matching OS. Values: `linux`, `darwin`, `win32` (Node.js `process.platform`) |
| `always` | `boolean` | If `true`, skip all `requires` checks — always show (but `os` still applies) |
| `requires.bins` | `string[]` | ALL must be present in `$PATH`. Skill hidden if any missing. |
| `requires.anyBins` | `string[]` | At least ONE must be present in `$PATH`. |
| `requires.env` | `string[]` | ALL must be set (in env, skill config env, or via apiKey + primaryEnv). |
| `requires.config` | `string[]` | ALL must be truthy in OpenClaw config (dot-path notation). |

**All `requires` checks are AND-ed** — every category must pass.

## Evaluation Order

1. `os` check — reject if platform doesn't match
2. `always` check — if `true`, approve immediately
3. `requires` check — bins → anyBins → env → config (all must pass)

## Real Examples

### Skill requiring `gh` CLI and GitHub token
```yaml
metadata: |
  {
    "openclaw": {
      "requires": {
        "bins": ["gh"],
        "env": ["GH_TOKEN"]
      }
    }
  }
```

### macOS-only skill
```yaml
metadata: |
  {
    "openclaw": {
      "os": ["darwin"]
    }
  }
```

### Skill requiring Telegram channel configured
```yaml
metadata: |
  {
    "openclaw": {
      "requires": {
        "config": ["channels.telegram"]
      }
    }
  }
```

### Skill requiring at least one browser binary
```yaml
metadata: |
  {
    "openclaw": {
      "requires": {
        "anyBins": ["chromium", "google-chrome", "firefox"]
      }
    }
  }
```

## Current Gaps (not yet supported natively)

| Feature | Status | Workaround |
|---------|--------|------------|
| `fallback_for_tools` — show when a tool is MISSING | Not supported | Use `requires.config` pointing to a flag you set |
| `requires_tools` — show when an OpenClaw tool exists | Not supported | Use `requires.bins` for CLI-equivalent check |

These gaps are candidates for an upstream OpenClaw feature request.

## Scripts

### Audit all skills and their conditional status
```bash
uv run python skills/conditional-skills/scripts/audit_skills.py
```

Shows which skills have conditional metadata and what they require.

### Check a single skill's conditions
```bash
uv run python skills/conditional-skills/scripts/check_conditions.py ~/.openclaw/workspace/skills/some-skill/
```

## When to Make a Skill Conditional

**Do** make conditional when:
- Skill needs a binary not on all machines (e.g., `gh`, `docker`, `ffmpeg`)
- Skill needs a paid API key (e.g., `OPENAI_API_KEY`)
- Skill is platform-specific (e.g., iMessage on macOS)
- Skill needs a specific channel configured (e.g., Discord, Telegram)

**Don't** make conditional when:
- Skill is pure Python with no external deps
- Skill reads from workspace files (always available)
- Skill provides guidance/docs only (no runtime dependency)
- You're not sure — unconditional is the safe default

## Verification
- Add metadata block → restart session → check if skill appears in available skills list
- Test negative case: unset an env var or remove a binary → confirm skill disappears
