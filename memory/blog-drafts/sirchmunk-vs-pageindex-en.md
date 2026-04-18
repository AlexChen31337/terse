# Index or Search Live? Two Approaches to Agent Knowledge Retrieval

*Published March 2026 | Analysis based on project documentation — not hands-on benchmarks*

---

## The Problem Every Agent Builder Hits

You've built an agent. It's smart, it's fast, and it's connected to your codebase or documentation. Then it needs to find something — a function definition buried three directories deep, a config value scattered across five files, a concept mentioned in docs written six months ago.

This is where most agent pipelines quietly break down. Not because the LLM can't reason about the content — it absolutely can. The bottleneck is *getting the right content in front of the model* in the first place. Retrieval is the unsexy problem that determines whether your agent is actually useful or just impressive in demos.

Two distinct schools of thought have emerged for solving this. They make fundamentally different bets about where the cost should be paid.

---

## School One: Index First (PageIndex)

The traditional approach — and still the dominant one in production systems — is to build an index upfront. PageIndex represents this philosophy: before any queries happen, you process your corpus (code, docs, knowledge base) into a structured vector or graph index. Embeddings are computed, relationships mapped, chunks stored.

When a query comes in, retrieval is deterministic and fast. Milliseconds, not seconds. The index does the heavy lifting, and the LLM only sees pre-filtered, highly relevant chunks.

This approach works exceptionally well when:
- Your corpus is large (millions of tokens)
- The content is relatively stable
- Queries are frequent (amortizing the indexing cost)
- You need consistent, reproducible retrieval

The tradeoff is real though. Index-building costs time and compute upfront. More critically: your index reflects the state of your data *at indexing time*. If files change, the index goes stale. In an actively evolving codebase, you're either re-indexing constantly or trusting outdated information.

---

## School Two: Search Live (Sirchmunk)

Sirchmunk, released in March 2026 by ModelScope (Alibaba's open-source ML platform), takes the opposite bet. There's no index. When you ask a question, it searches your raw files directly — right now, in real time.

The mechanism is clever. It runs a ripgrep keyword cascade first: fast, deterministic grep-style search to identify candidate files. Then it applies **Monte Carlo evidence sampling** — essentially running multiple LLM-guided sampling passes over the candidates, building up probabilistic evidence about where the relevant information lives. The result combines deterministic keyword matching with contextual LLM reasoning, without requiring a pre-built index.

Two modes:
- **FAST mode:** 2-5 seconds, 2 LLM calls. Good for most queries.
- **DEEP mode:** 10-30 seconds, more sampling passes. For complex multi-hop retrieval.

The cost is paid per query, not upfront. Every search hits the live files. The data is always current. The setup cost is zero.

---

## Side-by-Side

| Dimension | PageIndex (index-first) | Sirchmunk (search-live) |
|---|---|---|
| **Setup cost** | High (build index first) | Zero |
| **Query latency** | Milliseconds | 2-30 seconds |
| **Data freshness** | Stale until re-indexed | Always live |
| **Cost model** | Pay once, query cheap | Pay per query (LLM calls) |
| **Scale** | Excellent for large corpora | Better for focused codebases |
| **Accuracy on changing data** | Degrades without re-index | Always accurate |
| **Infrastructure** | Vector DB or graph store required | Just ripgrep + LLM |
| **Setup complexity** | Moderate-to-high | Minimal |

---

## When to Use Which

**Use PageIndex when:**
- You have a large, stable knowledge base (internal wikis, API docs, legal documents)
- Query volume is high enough to amortize indexing cost
- Retrieval latency matters (sub-second responses required)
- You control re-indexing pipelines and can keep them fresh

**Use Sirchmunk when:**
- Your codebase or docs are actively changing (daily commits, frequent edits)
- You want zero infrastructure overhead — no vector DB, no embedding pipeline
- You're prototyping or running a small-to-medium agent over focused repos
- Stale index risk is unacceptable (e.g., debugging an agent against live code)
- Query volume is low enough that per-query LLM cost is manageable

**The rule of thumb:** If your data is changing faster than you'd realistically re-index it, Sirchmunk wins on accuracy. If your data is stable and queries are frequent, PageIndex wins on cost and latency.

For autonomous coding agents working against actively-developed repos, Sirchmunk's search-live model is genuinely compelling. The agent always sees the current state of the code — not a snapshot from last Tuesday.

---

## Where This Is Going

The fact that Sirchmunk exists at all — and was released just this month — signals something important: the ecosystem is starting to question whether index-first is always the right default.

As LLM inference gets faster and cheaper, the calculus shifts. A 5-second search that's always accurate starts to look better than a 50ms search that might be working from stale data. The per-query cost of running LLM reasoning over raw files will keep dropping.

The longer trend is probably toward hybrid approaches: use fast keyword-based filtering (ripgrep, BM25) to narrow the candidate set, then apply LLM reasoning over live content for the final retrieval step. Sirchmunk is already doing this — it's just not using a pre-built semantic index.

Index-first isn't going anywhere. For large, stable knowledge bases, it's still the right tool. But search-live is a legitimate alternative for agent workloads that couldn't tolerate stale data anyway.

Knowing which one to reach for — that's the new skill.

---

*This post is based on analysis of project documentation. Sirchmunk (v0.0.6) was released March 12, 2026 via ModelScope. PageIndex represents a general architectural pattern, not a specific product.*
