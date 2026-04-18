# Intelligent Router Bug — February 16, 2026 08:35 AEDT

## Critical Bug Found

**Task:** "design scalable microservices architecture with service mesh, API gateway, and distributed tracing across 12 services"

**Expected:** COMPLEX tier (architectural design, multi-component, high complexity)

**Actual:** SIMPLE tier (4.62% confidence, weighted score 0.122)

## Root Cause Analysis

Scoring breakdown shows:
- **Simple Indicators:** 1.000 (inverted, meaning NO simple indicators found — this is correct)
- **Technical Terms:** 0.500 (detected "architecture", "microservices", "API", etc.)
- **Code Presence:** 0.333 (some detection)
- **Imperative Verbs:** 0.000 ❌ — "design" should trigger this
- **Multi-Step Patterns:** 0.000 ❌ — "with X, Y, and Z" is multi-component
- **Domain Specificity:** 0.000 ❌ — "microservices", "service mesh", "distributed tracing" are highly domain-specific

## Missing Detection Patterns

**Imperative verbs not caught:**
- "design" (architecture verb)
- "architect" (should be strongest signal)

**Architecture keywords not weighted properly:**
- "architecture" — should be STRONG COMPLEX signal
- "scalable" + "distributed" — system design markers
- "microservices" — architectural pattern

**Multi-component indicators:**
- "with X, Y, and Z" pattern
- "across 12 services" — explicit multi-component mention

## Proposed Fix

Update `router.py` scoring logic:

1. **Add architecture detection:**
   - Keywords: "architecture", "architect", "design system", "design scalable"
   - Weight boost: +0.3 to score if detected

2. **Improve imperative verb detection:**
   - Add: "design", "architect", "plan", "structure"

3. **Add multi-component pattern:**
   - Regex: `with .+ and .+` → Multi-Step Patterns dimension
   - Regex: `across \d+ (services|components|systems)` → Domain Specificity

4. **Domain specificity boost:**
   - List: "microservices", "service mesh", "API gateway", "distributed tracing", "kubernetes", "docker", "CI/CD"

## Impact

**Current bug causes:**
- Cost waste: Using expensive models (Opus/Sonnet) for SIMPLE tasks incorrectly
- Quality risk: Using cheap models (GLM) for COMPLEX tasks incorrectly
- Loss of trust in router recommendations

**Severity:** HIGH — Core functionality broken for architectural tasks.

## Testing After Fix

```bash
# Should classify as COMPLEX
python3 skills/intelligent-router/scripts/router.py classify \
  "design scalable microservices architecture with service mesh"

# Should classify as MEDIUM
python3 skills/intelligent-router/scripts/router.py classify \
  "fix bug in authentication middleware"

# Should classify as SIMPLE  
python3 skills/intelligent-router/scripts/router.py classify \
  "check server status"
```

## Status

**Logged:** February 16, 2026 08:35 AEDT  
**Assigned:** Alex Chen (self)  
**Priority:** HIGH  
**Action:** Fix router.py scoring logic properly (no quick fixes)

— Alex Chen
