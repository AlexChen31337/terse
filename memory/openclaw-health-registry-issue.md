# OpenClaw Issue: Intelligent Model Health Tracking & Fallback

## Feature Request: Circuit Breaker Pattern for Model Selection

### Problem

When spawning sub-agents with a specific model (e.g., `sessions_spawn` with `model: "Sonnet-Proxy2"`), if that model fails (quota exhausted, rate limited, etc.), the sub-agent task fails immediately with no automatic fallback to alternative models.

**Current behavior:**
```
Sub-agent spawn → Model fails (400 quota exhausted) → Task fails → No retry
```

**Example error from production:**
```json
{
  "stopReason": "error",
  "errorMessage": "400 {\"type\":\"error\",\"error\":{\"type\":\"BadRequest\",\"message\":\"Resource Package Exhausted\"}}"
}
```

While `agents.defaults.model.fallbacks` exists for the main session, sub-agents with explicitly specified models don't benefit from fallback chains.

### Proposed Solution

Implement a **circuit breaker pattern** with health tracking for all model endpoints:

#### 1. Model Health States

```
HEALTHY → (N consecutive failures) → DEGRADED → (cooldown expires) → HEALTHY
                                         ↓
                                   (success) → HEALTHY
```

#### 2. Health Registry

Track per-model:
- State: `healthy` | `degraded` | `unknown`
- Consecutive failures
- Last failure/success timestamps
- Error types (quota, rate limit, timeout, etc.)
- Success rate (for tie-breaking)

#### 3. Intelligent Fallback

When spawning sub-agent or making model calls:
1. Check if requested model is healthy
2. If degraded, try fallbacks in order
3. If all degraded, pick model with best historical success rate
4. Auto-recover degraded models after cooldown period

### Configuration

```json
{
  "agents": {
    "defaults": {
      "health": {
        "enabled": true,
        "failureThreshold": 3,
        "cooldownPeriod": "5m",
        "autoRecover": true,
        "persistState": true
      },
      "subagents": {
        "model": {
          "fallbacks": [
            "anthropic-proxy-4/glm-4.7",
            "nvidia-nim/deepseek-ai/deepseek-v3.2",
            "ollama/qwen2.5:32b"
          ]
        }
      }
    }
  }
}
```

### API Surface

```typescript
// Internal - track model health
modelHealth.recordSuccess(modelId: string): void
modelHealth.recordFailure(modelId: string, errorType: string): void
modelHealth.isHealthy(modelId: string): boolean
modelHealth.getHealthyModel(preferred: string, fallbacks: string[]): string

// Status endpoint
GET /status → includes model health summary
GET /health/models → detailed model health states
```

### Benefits

1. **Resilience**: Tasks don't fail due to temporary model issues
2. **Cost efficiency**: Don't waste tokens on failing endpoints
3. **Self-healing**: Degraded models auto-recover after cooldown
4. **Observability**: Track which models are problematic

### Prior Art

We've implemented this pattern in [EvoClaw](https://github.com/clawinfra/evoclaw) at `internal/router/health.go` with:
- Circuit breaker with configurable thresholds
- Error classification (quota, rate limit, timeout, auth, etc.)
- Persistent health state across restarts
- Thread-safe operations

Happy to contribute a PR if there's interest in this feature.

### Related

- Similar to service mesh circuit breaker patterns (Istio, Envoy)
- Complements existing `model.fallbacks` config
- Could integrate with `/status` health checks

---

**Environment:**
- OpenClaw version: 2026.2.13
- Use case: Sub-agent orchestration with multiple model providers

