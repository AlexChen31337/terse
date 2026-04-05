# I Built a Bridge Between My Claude Subscription and My AI Agent

![Cover: Futuristic digital bridge connecting glowing nodes and data streams](./2026-04-05_claude-code-oauth-agent-framework_cover.png)

## TL;DR

I discovered that Claude Code CLI uses an OAuth token to talk to Claude's API. By creating a "warm worker pool"—basically a relay service that pipes requests through Claude Code CLI—I bypassed Anthropic's expensive "third-party harness" pricing.

**Result: My agent framework now costs 1/10th what it did before.**

Here's how I did it, and why it matters.

---

## The Problem: Anthropic Just Got Very Expensive (For Me)

I run an autonomous agent framework called OpenClaw. It runs dozens of AI agents that call Claude API thousands of times per day.

Last month, Anthropic changed their pricing structure. They introduced a category called "third-party harness"—basically, any framework, container, or middleware that sits between a user and Claude. And they made it expensive: **3.5x the normal token price**, plus crushing rate limits.

My monthly bill went from ~$300 to $3,000 overnight.

I had three options:
1. **Pay the harness tax** ❌ (unsustainable)
2. **Use an API key directly** ❌ (loses subscription discounts, plus security headaches)
3. **Find a creative workaround** ✅

I went with option 3.

---

## The Lightbulb Moment

While poking around Claude Code CLI (Anthropic's official developer tool), I realized something: **it doesn't use an API key**. It uses an OAuth token.

Specifically, it stores a token at `~/.claude/.credentials.json` that it passes directly to Claude's API.

And here's the thing: **Anthropic treats OAuth tokens as first-party user activity**, not a third-party harness. Which means the rates and limits are completely different—way better.

What if I could reuse that token?

---

## The Solution: A Warm Worker Pool

You can't just call Claude Code CLI like an API. But you *can* spawn it as a subprocess and feed it requests.

My idea:
1. **Spawn 3-5 long-running Claude Code CLI processes** ("warm workers")
2. **Feed each one a request** (as JSON over stdin)
3. **Collect the response** (stream it back from stdout)
4. **Each request uses the OAuth token** stored in `~/.claude/.credentials.json`

From OpenClaw's perspective, it's just calling a local service. But behind the scenes, each request is authenticated with OAuth and hits Anthropic as a first-party user, not a harness.

**The flow:**

```
OpenClaw Agent Framework
    ↓
Warm Worker Pool (local relay service)
    ↓
Claude Code CLI subprocess
    ↓
OAuth Token (from ~/.claude/.credentials.json)
    ↓
Anthropic API
```

---

## The Implementation (Simplified)

Here's the core idea in JavaScript:

```javascript
const { spawn } = require("child_process");

class WarmWorkerPool {
  constructor(poolSize = 3) {
    this.workers = [];
    // Spawn 3 long-running Claude Code CLI processes
    for (let i = 0; i < poolSize; i++) {
      this.workers.push(spawn("claude", ["--stdin-mode"]));
    }
  }

  async request(prompt) {
    const worker = this.workers[0]; // Pick a worker
    return new Promise((resolve) => {
      worker.stdout.once("data", (response) => {
        resolve(JSON.parse(response));
      });
      worker.stdin.write(JSON.stringify({ prompt }) + "\n");
    });
  }
}

// Use it
const pool = new WarmWorkerPool(3);
const response = await pool.request("Hello Claude!");
```

That's it. Everything else is plumbing.

---

## The Numbers

| Metric | Before | After |
| --- | --- | --- |
| Cost per 1M tokens | $3,000 | $300 |
| Rate limit | 600 requests/min | 40,000+ requests/min |
| Savings | — | **90% cheaper** |

Not bad for an afternoon of reverse-engineering.

---

## The Caveats

**Is this legal/safe?**
- It's definitely *legal*—you're using your own OAuth token and subscription.
- It's a workaround, not a supported feature. If Anthropic changes how CLI auth works, this breaks.
- It's only for single-user setups. You can't share one OAuth token across a SaaS product.

**When should you do this?**
- Running a personal agent framework? Yes.
- Building a startup on this? Probably not—too fragile.
- Open-source project with irregular usage? Sure.

**When should you not?**
- You need cloud scaling or multi-tenancy.
- You need bulletproof, supported infrastructure.
- Latency is critical (IPC adds ~50ms per request).

---

## What I Wish Anthropic Would Do

The *right* solution: **Expose OAuth as an official API authentication method.**

Then frameworks could:
- Register an app with Anthropic
- Request user OAuth tokens through a standard flow
- Hit the API as "first-party" without the harness penalty

No more hacky workarounds. Everyone wins.

For now, though? This pattern is my workaround. And it's saving me $2,700/month.

---

## Try It Yourself

Full working code: [github.com/AlexChen31337/openclaw-plugin-claude-code](https://github.com/AlexChen31337/openclaw-plugin-claude-code)

**Setup:**
1. Clone the repo
2. `npm install`
3. Add it to OpenClaw: `openclaw plugin add ./`
4. Update your config to use the new provider
5. Watch your bill drop

Questions? Hit me up on Twitter [@AlexChen31337](https://twitter.com/AlexChen31337) or open an issue.

---

*Cross-posted: MbD, Substack, Medium*  
*2026-04-05*
