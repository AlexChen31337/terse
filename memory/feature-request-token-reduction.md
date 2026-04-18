# Feature Request: System Prompt Token Overhead Reduction

**Filed:** 2026-04-18  
**Requested by:** Bowen Li  
**Current overhead:** ~8,000–10,000 tokens per request (fixed baseline)  
**Target:** ≤ 3,500 tokens fixed overhead  
**Motivation:** Comparable frameworks (e.g. Hermes) achieve 70–90% reduction via lazy-loading. OpenClaw's fixed overhead increases per-request cost and eats into model context window for actual work.

---

## Problem Analysis

### Current Token Budget Breakdown

| Component | Est. Tokens | Reducible? |
|-----------|-------------|-----------|
| Tool definitions (~30 tools + params) | 2,500–3,500 | ❌ Required for function calling |
| Available skills list (150 skills) | 1,500–2,000 | ✅ High impact |
| SOUL.md + USER.md + AGENTS.md | 800–1,200 | ✅ Medium impact |
| MEMORY.md injected inline | 600–900 | ✅ Medium impact |
| TOOLS.md + runtime metadata | 400–600 | ✅ Low-medium |
| Skills descriptions (compact format) | 600–800 | ✅ Covered above |
| **Total** | **~8,000–10,000** | |

**Hard floor:** Tool definitions (~2,500–3,500 tokens) cannot be removed as they are required for structured function calling.

**Realistic minimum:** ~3,000–3,500 tokens with all proposals applied.

---

## Proposals

### Proposal 1: Lazy-Loading Skill Router (HIGH PRIORITY)
**Savings: ~1,500–2,000 tokens**

**Current behaviour:** All 150 skill names + locations injected into every request as `<available_skills>` block.

**Proposed behaviour:**
- Remove the `<available_skills>` block from the fixed system prompt
- Add a new `skill_search(query: string) → Skill` tool that:
  1. Performs semantic search over skill descriptions
  2. Returns the top 1–3 matching SKILL.md contents
  3. Falls back to listing all skill names if no match
- The agent calls `skill_search` when it detects a task that may require a skill
- Skills are loaded on-demand, not pre-loaded

**Implementation notes:**
- Skill index is already built — the semantic search infra exists in the workspace
- Skills with high-frequency triggers (e.g. `taskflow`, `github`) could be pre-loaded for specific channels
- Cold-start latency: +1 tool call per session if a skill is needed; acceptable tradeoff

---

### Proposal 2: Memory On-Demand (HIGH PRIORITY)
**Savings: ~600–900 tokens**

**Current behaviour:** `MEMORY.md` (~600–900 tokens) is injected into every request via workspace file injection.

**Proposed behaviour:**
- Remove MEMORY.md from the always-injected workspace files
- The `memory_search` / `memory_get` tools already exist for recall
- Inject only a lightweight header: today's date + 3-line summary of active projects (auto-generated daily, ~100 tokens)
- Full MEMORY.md loaded only when explicitly needed (e.g. "what are my active projects?")

**Risk:** Agent may miss context it would have caught passively. Mitigation: daily summary injection preserves the most critical facts.

---

### Proposal 3: Minified Persona Block (MEDIUM PRIORITY)
**Savings: ~500–800 tokens**

**Current behaviour:** SOUL.md (~600 tokens) + USER.md (~300 tokens) + AGENTS.md (~800 tokens) injected separately, with significant overlap in rules.

**Proposed behaviour:**
- Merge into a single `CORE.md` (~300–400 tokens) containing only:
  - Agent name + owner name + timezone
  - 5–7 hard rules (no raw tool output, MbD gate, model quality rule, privacy rules)
  - Persona tone (2–3 sentences)
  - Delegation rules (1 paragraph)
- Move detailed rules (PBR pipeline, full model quality table, git history cleanup) to a `RULES.md` loaded on demand via a `rules_lookup` tool or when the task type matches

**Risk:** Loss of nuance in edge cases. Mitigation: rules are searchable, not gone.

---

### Proposal 4: Compressed Runtime Metadata (LOW-MEDIUM PRIORITY)
**Savings: ~200–400 tokens**

**Current behaviour:** Runtime block includes full tool availability list, capabilities, channel config, model aliases table, and workspace file list.

**Proposed behaviour:**
- Reduce to: `runtime: channel=telegram | model=claude-sonnet-4-6 | cwd=/media/DATA/.openclaw/workspace | tz=Australia/Sydney`
- Move model aliases to a `model_lookup(alias)` tool
- Remove full tool availability listing (agent already has tools via function calling schema)
- Remove workspace file list from runtime (agent discovers files via `exec ls` or `read` as needed)

---

### Proposal 5: Skill Description Compression (LOW PRIORITY)
**Savings: ~200–400 tokens**

**Current behaviour:** Each skill in `<available_skills>` has name + location + description (truncated to compact format, but still ~150 skills × ~20 tokens = ~3,000 tokens).

**Proposed behaviour (if Proposal 1 not implemented):**
- Keep only skill name + location (drop descriptions)
- Add description lookup via `skill_search` if needed
- Reduces from ~150 × 20 tokens → ~150 × 8 tokens = ~1,200 tokens

Note: This is a fallback if full lazy-loading (Proposal 1) is too complex to implement immediately.

---

## Expected Outcomes

| Scenario | Fixed Token Overhead |
|----------|---------------------|
| Current | ~8,000–10,000 |
| Proposals 1+2 only | ~4,500–5,500 |
| Proposals 1+2+3 | ~3,800–4,500 |
| All proposals | ~3,000–3,500 |

---

## Implementation Priority

1. **P1 — Lazy skill loading** (biggest win, standalone feature)
2. **P2 — Memory on-demand** (simple: just remove from workspace injection list)
3. **P3 — Minified persona** (requires new CORE.md authoring)
4. **P4 — Runtime compression** (requires gateway changes)
5. **P5 — Skill description drop** (only if P1 not done)

---

## Notes / Constraints

- Tool definitions cannot be reduced — they are structurally required by the Anthropic/OpenAI function calling API
- The "2,000 token" target mentioned by Bowen is not achievable with 30 tools; realistic floor is ~3,000–3,500
- Hermes' 70–90% reduction claim likely reflects fewer tools registered + lazy skill loading
- All proposals are backwards-compatible — the agent can still access full context on demand, it just doesn't pre-load it

---

*This document is for OpenClaw feature tracking. Forward to the OpenClaw team or file at https://github.com/openclaw/openclaw/issues.*
