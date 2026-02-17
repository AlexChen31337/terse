# EvoClaw Model Routing Fix - 2026-02-17

## Issue
EvoClaw agents (alex-hub, alex-eye) were using outdated provider names for GLM-4.7 models:
- alex-hub: `anthropic-glm-1/glm-4.7` 
- alex-eye: `anthropic-glm-2/glm-4.7`

Should have been using standardized proxy naming:
- alex-hub: `anthropic-proxy-4/glm-4.7`
- alex-eye: `anthropic-proxy-6/glm-4.7`

## Root Cause
1. **Config drift**: EvoClaw config was set up before the proxy-4/proxy-6 naming convention was established
2. **No documented standard**: The routing rule "all GLM models must use proxy-4 or proxy-6" was not documented in MEMORY.md
3. **State file caching**: Old agent state files cached the incorrect model names even after config update

## Fix Applied

### 1. Updated ~/.evoclaw-hub/config.json

**Renamed providers:**
```json
// Before:
"anthropic-glm-1": { ... }
"anthropic-glm-2": { ... }

// After:
"anthropic-proxy-4": { ... }
"anthropic-proxy-6": { ... }
```

**Updated routing:**
```json
"routing": {
  "simple": "anthropic-proxy-4/glm-4.7",
  "complex": "anthropic-proxy-6/glm-4.7",
  ...
}
```

**Updated agent definitions:**
```json
"agents": [
  {
    "id": "alex-hub",
    "model": "anthropic-proxy-4/glm-4.7",
    ...
  },
  {
    "id": "alex-eye",
    "model": "anthropic-proxy-6/glm-4.7",
    ...
  }
]
```

### 2. Cleared cached state
```bash
rm ~/.evoclaw-hub/data/agents/*.json
pkill -f "evoclaw --config"
cd ~/.evoclaw-hub && bash start.sh
```

### 3. Verified fix
```bash
curl -s http://localhost:8420/api/agents | python3 -c "..."
# Output:
# alex-hub: anthropic-proxy-4/glm-4.7
# alex-eye: anthropic-proxy-6/glm-4.7
```

## Outstanding Issue: Edge Agent Direct API Access

**Problem:** alex-eye (Pi edge agent) has hardcoded LLM config in `~/.evoclaw/start-agent.sh`:
```bash
export LLM_BASE_URL='https://api.z.ai/api/anthropic'
export LLM_API_KEY=$(cat ~/.evoclaw/llm-api-key)
export LLM_MODEL='glm-4.7'
```

**Why it exists:** Edge agents run LLM prompts locally and communicate results via MQTT, so they need their own LLM configuration.

**Decision needed:** 
- Option A: Leave edge agents with direct API access (exception to proxy routing rule)
- Option B: Make edge agents proxy through orchestrator (requires architecture change)
- Option C: Update edge agent to use proxy-4 or proxy-6 API keys

## Why This Wasn't In Memory

### Investigation Results

**What I checked:**
1. ✅ MEMORY.md - No routing rules documented
2. ✅ Daily notes (2026-02-*.md) - Only historical proxy references
3. ✅ HEARTBEAT.md - No routing rules
4. ✅ Workspace files - No routing documentation

**What I found:**
- `skills/intelligent-router/config.json` HAS the correct proxy-4/proxy-6 naming
- Historical references to proxy failovers exist but no explicit rule
- The naming convention was implicit, not documented

**Root cause:**
- **Implicit knowledge gap**: The rule "GLM models use proxy-4/6" existed in practice but wasn't written down
- **No canonical routing document**: There's no single source of truth for model routing rules
- **Memory consolidation missed it**: Since it wasn't explicitly stated in conversations, it didn't make it into MEMORY.md

## Lesson Learned

**New rule to add to MEMORY.md:**
```
Model Routing Standards:
- GLM models: Must use anthropic-proxy-4 or anthropic-proxy-6
- DeepSeek models: Use nvidia-nim provider when available
- Claude models: Use anthropic-proxy-1/2/3 or anthropic-oauth
- Never use direct z.ai URLs except for edge agents (pending review)
```

**Process improvement:**
1. When updating config, document the "why" not just the "what"
2. Routing rules should be in MEMORY.md as "Critical Lessons"
3. Health checks should verify model routing compliance, not just model presence

## Verification

**Before fix:**
```
alex-hub: zhipu-1/glm-4.7 (wrong)
alex-eye: zhipu-1/glm-4.7 (wrong)
Pi agent: Direct z.ai API (wrong)
```

**After fix:**
```
alex-hub: anthropic-proxy-4/glm-4.7 ✅
alex-eye: anthropic-proxy-6/glm-4.7 ✅
Pi agent: Direct z.ai API ⚠️ (pending decision)
```

## Follow-up Actions

1. [ ] Add model routing rules to MEMORY.md
2. [ ] Decide on edge agent routing policy
3. [ ] Update health check to verify routing compliance
4. [ ] Document why proxy-4/6 exist (load balancing? different API keys?)

---

**Fixed by:** Alex Chen
**Date:** 2026-02-17 10:02 AM AEDT
**Config backup:** ~/.evoclaw-hub/config.json.backup-20260217-095931
