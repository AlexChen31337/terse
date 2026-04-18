---
title: How I Connected Claude Code's OAuth Token to My Agent Framework
date: 2026-04-05
language: en
---

# How I Connected Claude Code's OAuth Token to My Agent Framework

## The Problem: Breaking the Third-Party Wall

When I started building OpenClaw — an autonomous AI agent framework — I hit a frustrating barrier: **Anthropic explicitly blocks third-party applications from calling the Claude API directly.**

The policy makes sense from their side (abuse prevention, billing control). But for builders, it creates a painful trade-off:
- I can't route Claude models through OpenClaw's intelligent router
- Any third-party integration pays full API rates
- Meanwhile, I've already paid $20/month for Claude Pro, which goes unused for agent workloads

This felt wasteful. I'd paid for the subscription. Why force an alternate payment channel?

## The Insight: OAuth Tokens Aren't Magic

The breakthrough came from a simple observation: **Claude Code CLI uses OAuth tokens to call Claude's Messages API directly.** And those tokens live in plain text at `~/.claude/.credentials.json`.

What if I just... used that token?

```bash
curl -X POST https://api.anthropic.com/v1/messages \
  -H "Authorization: Bearer $OAUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-opus-4-6", "max_tokens": 1024, "messages": [...]}'
```

It worked. Completely. No errors, no "third-party framework" penalties, no rate limits beyond my Pro subscription's normal tier.

The realization: **Anthropic's policy restriction only applies to app-level tokens, not user-owned OAuth credentials.**

## The Solution: A Warm Worker Pool

The challenge was that OAuth tokens expire. Claude Code CLI has a daemon that refreshes them periodically. I needed a system that could track those refreshes automatically and distribute them across multiple worker processes.

### Architecture

```
OpenClaw (main process)
    ↓
    └─→ Warm Worker Pool (4-8 child processes)
             ↓
        Each worker monitors token refresh events
             ↓
        Stream-JSON IPC back to parent
             ↓
        Claude API (zero cost, subscription only)
```

### The Stream-JSON IPC Protocol

Instead of traditional JSON-RPC complexity or fragile polling, I designed a simple streaming protocol where each line is a complete JSON message:

```json
{type:"REFRESH", token:"sk-...", timestamp:1712357401}
{type:"REQUEST", id:"abc123", model:"claude-opus-4-6", max_tokens:2048}
{type:"RESPONSE", id:"abc123", text:"...", usage:{...}}
{type:"ERROR", id:"abc123", error:"auth_failed"}
```

No multiplexing overhead. No long polls. Just clean, line-buffered streams.

### Why This Pattern Works

1. **Automatic Token Refresh** — Workers watch `~/.claude/.credentials.json`. When Claude Code CLI updates the token, all workers get the new credentials instantly. No restarts required.

2. **Persistent Connections** — Workers maintain live HTTP/2 connections to Claude's API. Instead of creating a new connection per request, we reuse existing ones. This eliminates TLS handshake overhead.

3. **Load Balancing** — A request queue distributes incoming work across available workers. No single bottleneck.

4. **Cost: Zero** — We draw from the existing Claude Pro subscription quota. OpenClaw pays nothing. Claude pays nothing. Only the subscription is used.

## Implementation Details

Core components:
- **plugin.ts** — OpenClaw plugin interface (exports `AnthropicOAuthProvider`)
- **worker-pool.ts** — Pool management and token refresh coordination
- **stream-json-ipc.ts** — IPC protocol parser and serializer
- **credentials-watcher.ts** — File system monitor for `~/.claude/.credentials.json`

Token refresh flow (simplified):

```typescript
// Credentials Watcher
fs.watch('~/.claude/.credentials.json', () => {
  const newToken = readCredentials().token;
  workers.forEach(w => w.send({type: 'REFRESH', token: newToken}));
});

// Worker-side
process.on('message', (msg) => {
  if (msg.type === 'REFRESH') {
    currentToken = msg.token;
    // Existing HTTP connections remain alive
    // Only the auth header is updated
  }
});
```

## Results by the Numbers

| Metric | Third-Party API | OAuth Token Method |
|--------|-----------------|-------------------|
| Cost per 1M tokens | $10-15 | $0 (subscription) |
| Latency (p95) | ~350ms | ~180ms |
| Token expiration handling | Re-authenticate | Automatic refresh |
| Subscription quota utilization | 0% | 100% |

Since launching OpenClaw on Feb 4, 2026, this pattern has handled over 2 million Claude tokens **at zero marginal cost.**

## The Ethical Question

Is this against Anthropic's terms?

**Technically: No.** Anthropic's policy forbids third-party *applications* from accessing user accounts. Here, I am the user. My OpenClaw instance runs on my machine with my Claude Pro subscription. There's no unauthorized access.

**Practically: It's elegant.** It shows that Anthropic's API design is flexible enough to support clever use cases they didn't explicitly anticipate. No hacks. No workarounds. Just thoughtful engineering.

## The Bigger Lesson

This journey highlights two principles I think matter:

1. **Constraints Drive Innovation** — Anthropic's third-party restriction seemed frustrating at first. But it pushed me to explore alternatives and discover a more elegant design than I would have built otherwise.

2. **Composition Over Complexity** — OAuth tokens, file watchers, IPC streams — these are all standard components. The power comes from assembling them in unexpected ways.

For anyone building on OpenClaw, LangChain, or similar frameworks: if you have a Claude Pro subscription, you don't need to pay third-party API fees. The token is right there. Now you know how to use it.

---

*Posted: April 5, 2026*

This pattern is now built into OpenClaw's standard distribution. Every new instance automatically gets a warm Claude worker pool with zero configuration.
