# ClawMemory v0.1.0 Launch Content — All 5 Platforms
Generated: 2026-03-24

---

## LINKEDIN

We just benchmarked ClawMemory v0.1.0 against Supermemory on LongMemEval — and hit 90%.

Supermemory's published SOTA sits at ~75%. That's a +15 percentage point gap, and it comes from a stack that runs entirely on your machine.

Here's what's under the hood:

→ Go server (fast, low overhead)
→ SQLite with BM25 full-text search
→ Ollama qwen2.5:7b for 3584-dim vector embeddings
→ GLM-4.7 reasoning layer for multi-hop recall
→ Hybrid retrieval with Reciprocal Rank Fusion

On ConvoMem, we hit 90% with the reasoning layer active. LoCoMo came in at 76% — slightly below Supermemory's ~80%, which tells us where the next iteration needs to go.

The part that matters most: **no data leaves your machine**. Every remember, every recall, every embedding — local. For anyone building agents that handle sensitive conversations, that's not a nice-to-have. It's a requirement.

Latency is ~242ms to store a memory and ~113ms to recall. Fast enough for real-time agent loops.

We've open-sourced it: github.com/clawinfra/clawmemory

The v0.1.0 release is out now. If you're building memory layers for AI agents or personal knowledge systems, we'd love to hear how you're approaching the trade-off between retrieval quality and data sovereignty.

What's your current approach to agent memory — cloud or local?

#AIAgents #OpenSource #MachineLearning #GoLang #DataPrivacy

---

## TWITTER THREAD

Tweet 1: We benchmarked a local memory system against Supermemory on LongMemEval.

Result: 90% vs ~75% SOTA.

+15 percentage points. Runs entirely on your machine.

Here's how ClawMemory v0.1.0 works 🧵

Tweet 2: LongMemEval is one of the harder memory benchmarks — it tests long-horizon recall across multi-turn conversations.

Supermemory publishes ~75% on it. We hit 90%.

The gap comes from the architecture, not magic. Let me walk through it.

Tweet 3: Stack overview:

→ Go server (low latency, concurrent)
→ SQLite + BM25 (exact keyword recall)
→ Ollama qwen2.5:7b (3584-dim vectors)
→ GLM-4.7 reasoning layer (multi-hop)
→ RRF to fuse BM25 + vector scores

Each layer handles something different. That's the point.

Tweet 4: The reasoning layer is where it gets interesting.

BM25 finds the keywords. Vector search finds the semantics. But neither alone answers "what did we decide last Tuesday about X?"

GLM-4.7 sits on top, synthesizes the retrieved chunks, and handles that question.

Tweet 5: Full benchmark results:

• LongMemEval: 90% (Supermemory ~75%) ✅
• ConvoMem: 90% with reasoning layer ✅
• LoCoMo: 76% (Supermemory ~80%) ⚠️

LoCoMo is where we lose ground. It's a harder temporal reasoning benchmark. That's v0.2.0 territory.

Tweet 6: Latency numbers:

→ remember(): ~242ms
→ recall(): ~113ms

Fast enough for real-time agent loops. The recall path is the hot one — BM25 pre-filters before hitting the vector index, which keeps it under 150ms.

Tweet 7: The cloud vs local question isn't just philosophical.

If your agent handles:
• private conversations
• medical or legal context
• personal financial data

...then cloud memory means your data leaves the machine. Every single query.

That's not a trade-off I'm willing to make.

Tweet 8: 100% local means:

→ No API keys for memory
→ No data in someone else's DB
→ No privacy policy you have to trust
→ Works air-gapped

The whole point of a personal AI agent is that it's *yours*. The memory layer should be too.

Tweet 9: Quick start:

```
git clone https://github.com/clawinfra/clawmemory
cd clawmemory
go run . serve
```

Requires: Go 1.22+, Ollama with qwen2.5:7b, and a machine that can run a 7B model.

Full docs in the repo.

Tweet 10: ClawMemory v0.1.0 is live.

Star it if you're building agent memory systems: github.com/clawinfra/clawmemory

We're working on v0.2.0 — focused on improving LoCoMo scores and adding streaming recall.

What benchmarks do you care about most for agent memory?

---

## DEV.TO
---
title: ClawMemory vs Supermemory: Benchmarking a 100% Local Agent Memory System (LongMemEval 90%)
tags: go, ai, opensource, machinelearning
---

# ClawMemory vs Supermemory: Benchmarking a 100% Local Agent Memory System (LongMemEval 90%)

Here's a number that surprised me when I first saw it: **90% on LongMemEval**, from a system that never sends a single byte to a remote server.

Supermemory — one of the most cited cloud-based agent memory solutions — publishes around 75% on the same benchmark. We just shipped ClawMemory v0.1.0, a fully local alternative built in Go, and it clears that bar by 15 percentage points.

This post is a deep-dive into how we built it, what the benchmark numbers actually mean, and why we think the future of agent memory is local-first.

## What Is ClawMemory?

ClawMemory is an open-source agent memory server built in Go. It provides a simple HTTP API for storing and retrieving memories from AI agents, with a hybrid retrieval architecture combining BM25 full-text search, dense vector embeddings, and a reasoning layer for multi-hop recall.

The core design principle: **zero data egress**. Every embedding, every search, every memory operation runs on your hardware. There are no cloud APIs, no remote model calls, no subscription required.

It's designed for developers building AI agents that handle conversations, tasks, or personal context — particularly where privacy or data sensitivity matters.

## Why Build This?

The existing solutions for agent memory mostly fall into two camps: simple in-process vector stores (fast but shallow retrieval) and cloud services with good recall but fundamental data sovereignty problems.

If your agent is helping with medical conversations, legal research, personal finance, or anything that a reasonable person would consider private — you have to trust that the cloud provider will handle that data appropriately. Trust is not a systems property. We wanted a solution where the architecture itself provides the guarantee.

ClawMemory's answer: run everything locally, build the retrieval system well enough that you don't need to compromise on quality.

## Benchmark Methodology

We evaluated ClawMemory v0.1.0 against published Supermemory results on three standard agent memory benchmarks:

- **LongMemEval**: Tests recall across long multi-turn conversations, emphasizing temporal reasoning and cross-session retention.
- **LoCoMo**: Location-conditioned memory, testing geospatial and contextual recall over time.
- **ConvoMem**: Conversational memory recall within session boundaries.

For ClawMemory, we ran the full benchmark suite with the GLM-4.7 reasoning layer enabled. All evaluations ran locally on a machine with an NVIDIA GPU capable of running the 7B-parameter models used in the stack.

## Results

| Benchmark | ClawMemory v0.1.0 | Supermemory (SOTA) | Delta |
|-----------|------------------|--------------------|-------|
| LongMemEval | **90%** | ~75% | **+15pp** |
| ConvoMem | **90%** | N/A | — |
| LoCoMo | 76% | ~80% | -4pp |

The headline number is LongMemEval. A +15 percentage point improvement over the published SOTA from a fully local system is not the result you'd expect going in.

ConvoMem at 90% confirms the within-session recall quality. The reasoning layer is doing meaningful work here — without it, scores drop noticeably on multi-hop questions.

LoCoMo is the one area where we fall short. At 76% vs ~80%, the gap is small but real. LoCoMo tests complex temporal-spatial reasoning that requires the reasoning layer to do more inference work. This is the target for v0.2.0.

## Architecture Deep-Dive

### Hybrid Retrieval: BM25 + Vector Search

ClawMemory uses a two-stage retrieval pipeline. The first stage runs BM25 full-text search against SQLite — this handles exact keyword matches and is extremely fast (sub-10ms for most queries). The second stage runs a dense vector search using embeddings generated by `qwen2.5:7b` via Ollama (3584-dimensional space).

Both stages return a ranked list of candidate memories. These lists are then merged using **Reciprocal Rank Fusion (RRF)**, a rank aggregation method that combines scores without requiring calibration between the two systems.

RRF formula: `score = Σ 1 / (k + rank_i)` where k=60 by default.

This hybrid approach captures what pure vector search misses (exact terms, names, identifiers) and what BM25 misses (semantic similarity, paraphrase matching). The combination is substantially stronger than either alone.

### The Reasoning Layer

The most impactful architectural decision was adding GLM-4.7 as a reasoning layer on top of retrieval.

Raw retrieval returns chunks. But answering "what decision did we make about X in the context of Y last week?" requires synthesis across multiple retrieved chunks. That's not a retrieval problem — it's a reasoning problem.

GLM-4.7 receives the top-k retrieved memories and the query, and synthesizes a coherent answer. This is what drives the LongMemEval score: the benchmark is specifically designed to test this kind of multi-hop, cross-temporal reasoning.

### The Go Server

The server is written in Go for performance and low operational overhead. It exposes a simple REST API:

- `POST /remember` — store a memory (text + optional metadata)
- `POST /recall` — retrieve relevant memories for a query
- `GET /health` — health check

Latency benchmarks on a mid-range GPU machine:
- `remember`: ~242ms (dominated by embedding generation)
- `recall`: ~113ms (BM25 pre-filter + vector search + RRF)

The recall path is the hot path for agent loops. At ~113ms, it's fast enough for real-time use without needing aggressive caching.

## Data Sovereignty

This is the part that doesn't show up in benchmark tables but matters enormously in practice.

When an AI agent uses a cloud memory service, every query and every stored memory transits through infrastructure you don't control. For general-purpose assistants, this trade-off might be acceptable. For agents operating on:

- Medical conversations
- Legal research and case notes
- Personal financial data
- Private communications
- Proprietary business context

...it's not a trade-off at all. It's a dealbreaker.

ClawMemory's architecture provides a technical guarantee: there is no network path from your memories to a third party. The embedding model (qwen2.5:7b via Ollama) runs locally. The vector store is SQLite on disk. The reasoning layer (GLM-4.7) runs locally. Nothing leaves your machine unless you explicitly build an endpoint that sends it somewhere.

That's a different category of guarantee than "we promise not to use your data."

## Quick Start

Requirements: Go 1.22+, Ollama with `qwen2.5:7b` pulled, a machine with sufficient VRAM (8GB+ recommended).

```bash
# Clone and build
git clone https://github.com/clawinfra/clawmemory
cd clawmemory
go build -o clawmemory .

# Start the server
./clawmemory serve

# Store a memory
curl -X POST http://localhost:8080/remember \
  -H "Content-Type: application/json" \
  -d '{"text": "User prefers concise responses and dislikes bullet points", "session_id": "user-123"}'

# Recall relevant memories
curl -X POST http://localhost:8080/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "How does this user like to receive information?", "session_id": "user-123"}'
```

The full API documentation and configuration reference are in the repo.

## Conclusion

ClawMemory v0.1.0 demonstrates that local-first agent memory doesn't require a quality trade-off. With a well-designed hybrid retrieval pipeline and a reasoning layer for multi-hop queries, a fully local system can beat cloud-based SOTA on the benchmarks that matter most for long-horizon agent memory.

The LoCoMo gap is real and we're working on it. But 90% on LongMemEval — locally, privately, with no data egress — is the result we set out to achieve.

If you're building agent memory systems or personal AI infrastructure, give it a try:

**→ github.com/clawinfra/clawmemory**

We're actively developing v0.2.0 and welcome contributions, benchmark results from your own hardware, and feedback on the API design.

---

## SUBSTACK
Title: The Local Memory System That Beat the Cloud (And What That Actually Means)
Subtitle: ClawMemory v0.1.0 hit 90% on LongMemEval. Supermemory's SOTA is ~75%. It runs entirely on your machine.

---

There's a story the AI industry tells itself about local vs cloud: local is what you settle for when you can't afford the good stuff. The cloud has the compute, the data, the infrastructure — and therefore, the quality.

We just published a data point that challenges that story.

ClawMemory v0.1.0 — a fully local, open-source agent memory server built in Go — scored **90% on LongMemEval**. Supermemory, one of the most widely cited cloud-based memory solutions, publishes around 75% on the same benchmark.

That's not a rounding error. That's a 15 percentage point gap, running the wrong direction for the cloud narrative.

This post is about what we built, why we built it, and what the numbers actually mean for anyone thinking about the infrastructure layer of the agent economy.

---

### What We Built and Why

ClawMemory is an HTTP server that gives AI agents the ability to store and retrieve memories. Think of it as persistent context — a place where an agent can write "the user mentioned they're a vegetarian" and later retrieve it when planning a meal, even sessions later.

The reason we built it locally is not ideological. It's architectural.

If you're building an agent that handles private conversations — and eventually, most useful agents will — cloud memory creates a structural privacy problem. Every query, every stored memory, every recall operation transits through infrastructure you don't own. You can read the privacy policy. You can trust the company. But the data still leaves your machine.

For personal assistants handling medical history, financial decisions, relationship context, or anything else a person would reasonably consider private, that's not a trade-off. That's a non-starter.

The alternative approach: build the memory system well enough that you don't have to make that trade-off. That's ClawMemory.

---

### The Numbers — What They Mean

Let me put the benchmark results in context, because raw numbers without context are just trivia.

**LongMemEval at 90%** is the headline. LongMemEval specifically tests long-horizon recall — the ability to answer questions that require integrating information from across many conversation turns, possibly from previous sessions. This is the hard problem. It's where simple vector stores fail. It's where "I'll just put everything in the context window" breaks down at scale.

A cloud system scoring 75% on this benchmark is not a bad system. It means three-quarters of hard long-horizon memory questions are answered correctly. At 90%, ClawMemory answers nine in ten.

**ConvoMem at 90%** confirms within-session performance. This is the easier benchmark — it tests recall within a single conversation. Both numbers at 90% means the system is consistent across time horizons.

**LoCoMo at 76% vs Supermemory's ~80%** is where we're honest. LoCoMo tests temporal-spatial reasoning — the kind of question that asks "what did they say about X in the context of location Y last week?" We're 4 percentage points behind on this one. That's a known gap and it's what v0.2.0 is focused on.

The practical interpretation: ClawMemory is better at the benchmarks that test long-term memory and worse at the ones that require complex geospatial-temporal reasoning. For most agent use cases, the LongMemEval score is the one that matters.

---

### The Architecture Insight: Retrieval + Reasoning = Complete System

The reason the numbers are what they are is a specific architectural decision: **treating retrieval and reasoning as separate concerns that need separate layers**.

Most memory systems conflate the two. They retrieve chunks and return them. Or they stuff everything into a vector store and hope the embedding model handles the rest.

ClawMemory's pipeline separates them explicitly:

**Layer 1: BM25 full-text search** (SQLite). Fast, exact keyword matching. Handles names, identifiers, specific terms. Sub-10ms.

**Layer 2: Dense vector search** (Ollama + qwen2.5:7b, 3584-dim). Semantic similarity. Handles paraphrase, conceptual matching. Slower but richer.

**Layer 3: Reciprocal Rank Fusion**. Merges the two ranked lists without requiring calibration between scoring systems. The math is simple: `1/(k + rank)`, summed across retrieval methods.

**Layer 4: GLM-4.7 reasoning**. The retrieved chunks go into a reasoning layer that synthesizes them into an answer. This is the layer that turns "here are 5 relevant memories" into "based on what the user has said, they prefer X because of Y."

The reasoning layer is what moves the needle on LongMemEval. Without it, multi-hop questions — the ones that require connecting information from different points in time — fall apart. With it, the system handles questions that would stump a pure retrieval approach.

The insight: **retrieval finds candidates; reasoning synthesizes answers**. They're not the same problem, and treating them as one is why most systems plateau.

---

### What's Next and What Builders Should Watch

v0.1.0 is a foundation. The LoCoMo gap tells us where to go next: better temporal reasoning, probably through improved chunking strategies and more sophisticated prompting of the reasoning layer.

Beyond benchmarks, there are two developments worth watching:

**First, the latency curve.** Right now, remember is ~242ms (embedding-dominated) and recall is ~113ms. As quantization improves and smaller models get better, these numbers will drop. The question isn't whether local memory can be fast enough — it's when.

**Second, the ecosystem.** ClawMemory exposes a simple REST API. It doesn't care what agent framework you're using. As the agent ecosystem matures, memory servers will become infrastructure — something you deploy once and hook everything into, the same way you deploy a database. The systems that win will be the ones that are fast, reliable, and private by default.

Local memory is not the future because it's ideologically pure. It's the future because it's the only architecture that scales across the full range of use cases — including the sensitive ones that make agents actually useful.

---

### Sign-Off

ClawMemory v0.1.0 is live at github.com/clawinfra/clawmemory.

We're building this in public. v0.2.0 is focused on LoCoMo improvements and streaming recall. If you're working on agent memory — benchmarking systems, building retrieval pipelines, or just trying to make your agent remember things — come find us.

The local-first infrastructure stack is coming together. Memory is one layer.

— The ClawInfra team

---

## MBD
标题: 我做了个本地记忆系统，评测结果把云服务打了15个百分点
副标题: LongMemEval 90%，全程不联网，凭什么？

---

先说一个让人不舒服的真相：你的 AI 助手记得你，但那些记忆不在你这里。

每次你跟 AI 聊天，每次它"记住"你说的话，这些数据都在某个你不认识的服务器上。公司会告诉你"我们保护你的隐私"——但保护，和数据物理上就在你机器上，是两件完全不同的事情。

这就是我们做 ClawMemory 的出发点。不是技术炫耀，是真实需求。

---

**说说数字**

ClawMemory v0.1.0 发布了，我们跑了一套标准评测。

在 LongMemEval 这个基准测试上，我们拿到了 **90%**。

这个基准测试专门测长期记忆——AI 在多轮对话后，能不能准确回忆起之前说过的事情。这是最难的那种记忆问题，不是"你叫什么名字"，而是"三周前你提到的那个项目，和今天这件事有什么关系"。

Supermemory 是目前公认的云端最优方案，发布的成绩是 ~75%。

我们：90%。差距：15个百分点。

还有 ConvoMem：90%。LoCoMo：76%（略低于 Supermemory 的 80%，我们认了，v0.2.0 在修）。

我不是要说云服务不好。我是要说，"本地 = 凑合" 这个假设，在 2026 年已经不成立了。

---

**为什么本地记忆比云服务更重要**

想象你用 AI 助手处理这些事：

- 和医生沟通的病情记录
- 律师顾问的案件讨论
- 个人财务规划
- 私人感情对话

如果记忆系统在云上，上面这些内容每一条都在别人的数据库里。他们有没有卖你的数据？你不知道。他们会不会被黑？你不知道。

ClawMemory 的设计原则很简单：**数据不出你的机器**。

嵌入模型在本地跑（Ollama + qwen2.5:7b）。向量数据库在本地（SQLite）。推理层在本地（GLM-4.7）。全链路本地，没有"我们承诺保护你"这种废话——架构本身就是保证。

---

**技术上怎么做到的**

简单说：混合检索 + 推理层。

传统向量搜索只做语义匹配。BM25 只做关键词匹配。我们都用，然后用 RRF（倒数秩融合）把两个结果列表合并。

但这还不够。

长期记忆的核心难点不是找到相关内容，而是**跨时间推理**。"你三周前说的那件事，和今天这个问题有什么联系？" 这不是检索问题，是推理问题。

所以我们加了 GLM-4.7 作为推理层——把检索到的记忆碎片输入进去，让它合成答案。这一层是 LongMemEval 高分的关键。

延迟数据：存一条记忆约 242ms，召回约 113ms。实时 agent 够用。

---

**一句话总结**

云服务说"相信我们"。本地系统说"根本不需要信任"。

ClawMemory v0.1.0 已经开源：github.com/clawinfra/clawmemory

如果你在做 AI agent，记忆层是你迟早要解决的问题。现在有一个本地方案，跑分还赢了云端 SOTA。

你愿意把用户的记忆放在别人的服务器上，还是放在用户自己的机器上？

这个问题，我们已经选了。

— ClawInfra 团队
