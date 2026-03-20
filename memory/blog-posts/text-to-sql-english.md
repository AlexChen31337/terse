# From 68% to ~100%: How We Built a Text-to-SQL System That Gets Smarter Every Day

*A practical guide to moving beyond vanilla LLM prompting toward a self-improving pipeline for production text-to-SQL.*

---

## The Problem with Vanilla LLM Text-to-SQL

We had what seemed like a straightforward problem: let business users ask natural-language questions about a large domain-specific table — hundreds of millions of rows, 200+ columns, a mandatory date filter on every query — and get back correct SQL. We started where most teams start: a well-crafted prompt, GPT-4, and a schema dump. It worked. Sort of.

Our initial accuracy was **~68%**. That sounds decent until you realize it means one in three queries returns wrong data. In a production system where people make decisions based on the output, 68% is unusable.

We identified three distinct failure modes that accounted for nearly all errors:

**1. Column hallucination.** With 200+ columns in the schema, the LLM would confidently reference columns that didn't exist or pick columns with similar names but different semantics. A column called `region_code` might get confused with `sales_region`, and the SQL would execute without errors — returning completely wrong results.

**2. Filter value errors.** Our domain table had dozens of categorical columns with specific enum values. The LLM would guess at values — writing `WHERE status = 'active'` when the actual value was `'Active'`, or `'sedan'` when the column stores `'Sedan'`. These queries return empty result sets, and the user has no idea why.

**3. Structural validity ≠ semantic correctness.** This is the insidious one. The SQL parses, executes, and returns rows. But it answers a subtly different question than the one asked. A year-over-year comparison that uses the wrong date boundaries. An aggregation that groups by the wrong dimension. The user gets a confident-looking table of numbers that happens to be wrong.

If you've followed the academic benchmarks, none of this is surprising. The BIRD benchmark — which evaluates text-to-SQL on messy, real-world databases — shows even the best published systems topping out around 72-75% execution accuracy on complex schemas. Our 68% was right in line with the state of the art for a single-prompt approach on a genuinely complex production schema.

The core issue is that **a single LLM call cannot reliably bridge the gap between ambiguous natural language and precise SQL** when the schema is large, the domain is specific, and the data has real-world messiness. Prompt engineering gets you to ~70%. Everything after that requires engineering.

We spent six months building what we now call "the pipeline" — eight components that, together, pushed our accuracy from 68% to a system that converges toward ~100% over time. Here's every component, what it does, and how much it contributed.

---

## The 8-Component Pipeline

### 1. Semantic Schema Linker (+~10%)

The single highest-leverage change we made was **stopping the LLM from seeing columns it doesn't need**.

With 200+ columns, the full schema description consumed most of the context window. Worse, it gave the LLM hundreds of opportunities to pick the wrong column. Our schema linker works like this: we pre-compute embeddings for every column name and its description. When a question comes in, we embed the question, compute cosine similarity against all column embeddings, and pass only the top-k most relevant columns (typically 20-30) to the LLM.

```typescript
async function linkSchema(question: string, allColumns: ColumnMeta[]): Promise<ColumnMeta[]> {
  const questionEmbedding = await embed(question);
  
  const scored = allColumns.map(col => ({
    ...col,
    similarity: cosineSimilarity(questionEmbedding, col.embedding),
  }));
  
  // Always include mandatory columns (e.g., date filter)
  const mandatory = scored.filter(c => c.isMandatory);
  const ranked = scored
    .filter(c => !c.isMandatory)
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, TOP_K);
  
  return [...mandatory, ...ranked];
}
```

The key insight: we **always include mandatory columns** (like the date filter) regardless of similarity score. Domain-specific invariants shouldn't depend on embedding quality.

This single component eliminated most column hallucination errors and gave us roughly **+10% accuracy** — the biggest single delta in the pipeline.

---

### 2. Question Masking + Semantic Few-Shot Retrieval (+~6%)

Generic few-shot examples ("Show me total sales by region") don't help when your domain has specific patterns. We needed **domain-specific examples** that match the structure of the incoming question, not just the topic.

The problem with naive semantic retrieval: "show me records from 2019" and "show me records from 2023" have different embeddings, but they need the exact same SQL pattern. Our solution was **question masking** — we replace numeric literals and proper nouns with placeholders before embedding.

```typescript
function maskQuestion(question: string): string {
  return question
    .replace(/\b\d{4}\b/g, '<YEAR>')          // mask years
    .replace(/\b\d+(\.\d+)?\b/g, '<NUM>')     // mask numbers
    .replace(/"[^"]+"/g, '<VALUE>')            // mask quoted values
    .replace(/\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+/g, '<ENTITY>'); // mask proper nouns
}
```

The masked form gets embedded and matched against a **pgvector store** of verified question→SQL pairs. Each pair in the store was human-verified as correct — more on that in the flywheel section.

Retrieving 3-5 semantically similar, domain-specific, verified examples gave us **+~6% accuracy**. The LLM went from guessing at patterns to following proven ones.

---

### 3. Pre-Execution LLM Self-Review (+~5%)

Even with a focused schema and good examples, the LLM still generates subtle errors on complex queries — wrong date boundaries in year-over-year comparisons, incorrect GROUP BY clauses, off-by-one errors in date ranges.

We added a **review step**: after the first LLM generates SQL, a second LLM pass reviews it. The reviewer sees the original question, the schema subset, and the generated SQL — but not the generation prompt. It answers: "Does this SQL correctly answer this question given this schema?"

```typescript
async function reviewAndRegenerate(
  question: string, 
  schema: ColumnMeta[], 
  sql: string,
  maxIterations: number = 3
): Promise<{ sql: string; confidence: number }> {
  
  for (let i = 0; i < maxIterations; i++) {
    const review = await reviewSQL(question, schema, sql);
    
    if (review.confidence >= 0.70) {
      return { sql, confidence: review.confidence };
    }
    
    // Regenerate with review feedback
    sql = await regenerateSQL(question, schema, sql, review.issues);
  }
  
  // Return best attempt with low confidence flag
  return { sql, confidence: 0.0 };
}
```

We call this the RRIL (Review-Regenerate-Iterate Loop). Max 3 iterations, confidence threshold of 0.70. If it can't reach 0.70 after 3 tries, it flags the query for human review.

This caught roughly **+5% of errors**, primarily on complex multi-condition queries where the first pass got 80% of the logic right but missed a subtle constraint.

---

### 4. Column Value Sampling (+~3-4%)

This one is embarrassingly simple and we should have built it first.

For every column detected as low-cardinality or enum-like (fewer than ~500 distinct values), we sample 20-50 actual values from the database and inject them into the prompt: *"The `status` column contains values: 'Active', 'Inactive', 'Pending', 'Archived'."*

```typescript
async function sampleColumnValues(
  column: ColumnMeta, 
  db: Database
): Promise<string[]> {
  const distinctCount = await db.query(
    `SELECT COUNT(DISTINCT "${column.name}") FROM domain_table`
  );
  
  if (distinctCount > MAX_ENUM_CARDINALITY) return [];
  
  const samples = await db.query(
    `SELECT DISTINCT "${column.name}" 
     FROM domain_table 
     WHERE "${column.name}" IS NOT NULL 
     LIMIT 50`
  );
  
  return samples.map(r => r[column.name]);
}
```

No more `'sedan'` vs `'Sedan'` mismatches. No more guessing at valid status codes. The LLM sees the actual values and uses them. **+3-4% accuracy**, and it's the cheapest component to implement.

---

### 5. Query Complexity Router (Quality + Cost)

Not every question needs the most expensive model. "How many records do we have this month?" is a simple COUNT with a date filter. "Compare year-over-year trends across the top five categories, broken down by quarter" requires genuine reasoning.

We classify incoming questions into three complexity tiers and route accordingly:

| Tier | Pattern | Model | ~Share |
|------|---------|-------|--------|
| Simple | Single aggregation, basic filter | Haiku (fast, cheap) | 60% |
| Medium | Domain filters, joins, grouping | Sonnet (balanced) | 30% |
| Complex | YoY, multi-breakdown, subqueries | Opus (highest quality) | 10% |

The classifier itself is a lightweight Haiku call — costs almost nothing and adds ~200ms of latency. The result: **~70% cost reduction** with zero accuracy loss. Simple queries don't benefit from Opus, and sending them there is pure waste.

---

### 6. Rule-Versioned Embedding Cache (Consistency)

Business rules change. A new mandatory filter gets added. A column gets deprecated. An enum value gets renamed. When this happens, cached question→SQL pairs can become stale or non-compliant.

Every cached pair is stored with a **rule version hash**. When the rules change (we increment a version), the system recomputes compliance scores for all cached pairs against the new rules and surfaces non-compliant ones for human review.

```typescript
interface CachedPair {
  question: string;
  maskedQuestion: string;
  sql: string;
  embedding: number[];
  ruleVersionHash: string;
  complianceScore: number;
  verifiedBy: string;
  verifiedAt: Date;
}

async function flagStale(currentRuleHash: string): Promise<CachedPair[]> {
  return await db.query(`
    SELECT * FROM cached_pairs 
    WHERE rule_version_hash != $1
    ORDER BY last_used_at DESC
  `, [currentRuleHash]);
}
```

This doesn't directly improve accuracy on new questions, but it **prevents regression** — which, in a production system, matters more than you'd think. A cached pair that was correct last month but violates a new mandatory filter is worse than no cache at all.

---

### 7. Pipeline Tracing (Observability)

Every query that flows through the pipeline generates a trace record:

- Which columns the schema linker selected
- Which few-shot examples were retrieved (and their similarity scores)
- The pre-review output (issues found, confidence score, iterations)
- The final SQL sent for execution
- Execution time, row count, token usage per LLM call

All stored as JSONB in the existing query log table. Zero new infrastructure dependencies.

```typescript
interface PipelineTrace {
  traceId: string;
  question: string;
  schemaColumns: string[];        // columns selected by linker
  fewShotExamples: string[];      // IDs of retrieved pairs
  reviewIterations: number;
  reviewConfidence: number;
  finalSQL: string;
  executionTimeMs: number;
  tokenUsage: { prompt: number; completion: number };
  modelUsed: string;
  cacheHit: boolean;
}
```

This doesn't improve accuracy directly, but it's what makes **debugging and improvement possible**. When a query fails, we can see exactly which component contributed to the failure. When accuracy dips, we can query the traces to find patterns. Without tracing, the pipeline is a black box. With it, every failure is a learning opportunity.

---

### 8. Prompt Prefix Caching (Latency + Cost)

The schema description, universal rules, and system instructions are identical across thousands of queries. Only the user's question and the retrieved few-shot examples change per request.

On Anthropic's API, we structure our prompts so the static portion comes first, then use prompt caching to avoid re-processing the prefix on every call. The schema description alone can be 3,000+ tokens — caching it means those tokens are processed once and reused.

Result: **~40% reduction in billable tokens** across all queries, with no impact on output quality. Combined with the complexity router, our per-query cost dropped dramatically.

---

## The Flywheel — Why This Beats Any Static Benchmark

The pipeline took us from 68% to roughly 89% on Day 1. That's a strong improvement, but it's still not production-grade. The component that pushed us toward ~100% wasn't a pipeline stage — it was a **feedback loop**.

After every query, the system evaluates its own confidence score from the review step. High-confidence results (≥0.85) are auto-approved and promoted into the embedding cache as verified pairs. Low-confidence results, or any result a user flags as incorrect, get routed to a human reviewer.

The reviewer sees the question, the generated SQL, the expected result, and — if the user provided a correction — the corrected SQL. They verify or fix the pair, and the corrected version gets promoted to the cache.

Here's why this is powerful: **the next time a semantically similar question arrives, it matches against the cached pair and short-circuits the entire pipeline**. No LLM call needed. The answer comes directly from a human-verified, production-tested pair.

The flywheel effect played out like this in our system:

| Time | Accuracy | Cache Hit Rate | LLM Calls |
|------|----------|----------------|-----------|
| Day 1 | ~89% | 0% | 100% |
| Week 4 | ~94% | ~40% | ~60% |
| Month 6 | ~97% | ~70% | ~30% |
| Stable state | ~99%+ | ~80-90% | ~10-20% |

The academic benchmarks like BIRD measure a frozen system — a fixed model, fixed prompt, fixed schema, evaluated once. Our system gets smarter every day. Every query that flows through it either confirms an existing cached pair or generates a new one (after human verification).

And here's the part that makes finance people happy: **cost falls as accuracy rises**. As the cache fills up, fewer queries need LLM calls. The most expensive component (Opus for complex queries) gets called less and less as the cache absorbs the patterns it's already seen. We're simultaneously improving quality and reducing cost — the flywheel improves both.

The cache currently holds thousands of verified pairs, and roughly 80-90% of incoming questions match an existing pair closely enough to skip the pipeline entirely. The remaining 10-20% are genuinely novel questions — new patterns the system hasn't encountered before. Those go through the full pipeline, get reviewed, and feed back into the cache.

---

## The Honest Ceiling

We don't claim 100% accuracy, and we never will. The remaining 1-3% of failures are genuinely hard problems:

**Novel query patterns.** When a user asks something structurally unlike anything in the cache, the system falls back to the full pipeline. Pipeline accuracy without cache assistance is ~89% — good, but not perfect. These novel patterns are, by definition, the hardest queries.

**Ambiguous natural language.** "Show me recent data" — does "recent" mean last week? Last month? Last quarter? The system can detect ambiguity (we added an ambiguity classification step), but resolving it requires either a clarifying question or a business-specific default. Both have trade-offs.

**Data drift.** New values appear in enum columns. A product category gets renamed. A new region code gets added. Our value sampling refreshes periodically, but there's always a window where the LLM has stale information. Continuous sampling narrows the window but can't eliminate it entirely.

Our approach to the ceiling: **human-in-the-loop is not a failure mode — it's the mechanism that closes the gap**. Low-confidence novel queries get flagged for human review. The human provides the correct SQL. The pair enters the cache. The system has learned. The ceiling rises.

---

## What We'd Do Differently

If we were starting over, three things would change:

**Start with value sampling.** It's the cheapest component to build (a few SQL queries, some prompt injection) and eliminates an entire category of errors. We built it fourth. It should have been first. Half a day of work for a 3-4% accuracy gain.

**Build tracing from Day 1.** We spent weeks debugging pipeline failures by staring at prompts and outputs manually. Once we had tracing, debugging time dropped by 10x. Every failure was immediately attributable to a specific component. Build the observability before you build the intelligence.

**Invest heavily in the schema linker.** It has the highest leverage of any component. A better schema linker means a smaller, more relevant context, which means better LLM output across all query types. We've iterated on ours four times and it's still the component we invest the most engineering time in.

---

## Closing

Production text-to-SQL is not a prompting problem. It's a systems engineering problem. The combination of **retrieval augmentation** (schema linking + few-shot retrieval), **pre-execution review** (the RRIL loop), and a **human feedback flywheel** (verified pairs that compound over time) is what makes near-perfect accuracy achievable in practice.

Static benchmarks measure the floor. The flywheel determines the ceiling.

If you're building text-to-SQL for a specific domain, the generic approach — a good prompt and a frontier model — will disappoint you. It'll get you to 70%, and you'll spend months trying to prompt-engineer your way to 80%. The path to production-grade accuracy is domain-specific retrieval, systematic error elimination, and a feedback loop that turns every query into a learning opportunity.

---

## Key Takeaways

- **Schema linking is the highest-leverage component.** Reducing 200+ columns to 20-30 relevant ones eliminates an entire class of hallucination errors. Build it first, invest in it continuously.

- **Value sampling is the cheapest win.** Injecting actual enum values into the prompt costs almost nothing to implement and eliminates case-sensitivity and value mismatch errors immediately.

- **The review loop catches what single-pass generation misses.** A second LLM pass reviewing the generated SQL against the original question catches 5%+ of subtle errors, especially on complex multi-condition queries.

- **The flywheel is the real product.** The pipeline gets you to ~89%. The human-in-the-loop feedback loop that populates a verified cache is what pushes you toward ~100% — and simultaneously reduces cost.

- **Observability is not optional.** Without pipeline tracing, you're debugging a black box. With it, every failure is attributable and fixable. Build tracing before you build intelligence.

---

*If you're working on a similar system, I'd love to hear about your approach — especially how you handle schema linking and the accuracy/cost tradeoff. Drop a comment or reach out.*
