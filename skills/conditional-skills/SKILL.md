---
name: conditional-skills
description: "Specification and tooling for conditional skill activation — skills that auto-show/hide based on available toolsets, tools, or platform."
version: 1.0.0
---

# Conditional Skills — Auto-Show/Hide Based on Environment

## When to Use
- Authoring a new skill that should only appear when certain tools are available (or missing)
- Debugging why a skill isn't showing up in the index
- Auditing which skills have conditional activation rules

## Specification

Skills can add optional conditional fields to their YAML frontmatter:

```yaml
metadata:
  openclaw:
    fallback_for_toolsets: [web]       # SHOWN only when these toolsets are UNAVAILABLE
    requires_toolsets: [terminal]       # SHOWN only when these toolsets are AVAILABLE
    fallback_for_tools: [web_search]   # SHOWN only when these tools are UNAVAILABLE
    requires_tools: [browser]          # SHOWN only when these tools are AVAILABLE
    platforms: [linux, macos]          # SHOWN only on matching OS
```

| Field | Behavior |
|-------|----------|
| `fallback_for_toolsets` | Skill HIDDEN when listed toolsets are available. SHOWN when missing. |
| `fallback_for_tools` | Same, but checks individual tools instead of toolsets. |
| `requires_toolsets` | Skill HIDDEN when listed toolsets are unavailable. SHOWN when present. |
| `requires_tools` | Same, but checks individual tools instead of toolsets. |
| `platforms` | Skill HIDDEN on non-matching OS. Values: `linux`, `macos`, `windows`. |

Skills **without** any conditional fields behave as before — always shown.

## Procedure

1. Decide if your skill genuinely needs conditional activation (most don't)
2. Add the appropriate `metadata.openclaw.*` fields to your SKILL.md frontmatter
3. Test both states — verify the skill shows when expected and hides when not
4. Run the audit script to confirm: `uv run python scripts/audit_skills.py`

## Examples

### DuckDuckGo fallback (shows only when web_search is unavailable)
```yaml
---
name: duckduckgo-search
description: "Free web search via DuckDuckGo — no API key needed."
metadata:
  openclaw:
    fallback_for_tools: [web_search]
---
```

### macOS-only skill
```yaml
---
name: imessage
description: "Send and receive iMessages on macOS."
metadata:
  openclaw:
    platforms: [macos]
---
```

### Skill requiring browser tool
```yaml
---
name: browser-automation
description: "Advanced browser automation workflows."
metadata:
  openclaw:
    requires_tools: [browser]
---
```

## Scripts

### Check conditions for a single skill
```bash
uv run python skills/conditional-skills/scripts/check_conditions.py ~/.openclaw/workspace/skills/some-skill/
```

### Audit all skills
```bash
uv run python skills/conditional-skills/scripts/audit_skills.py
```

## Pitfalls
- Don't make skills conditional unless there's a clear reason — unconditional is simpler
- Test both states (tool available AND missing) before shipping
- `platforms` uses lowercase: `linux`, not `Linux`
- Multiple conditions are AND-ed — all must pass for the skill to show

## Verification
- Run `check_conditions.py` on a skill with conditional fields → confirms visible/hidden with reasons
- Run `audit_skills.py` → see all conditional skills and their current state
