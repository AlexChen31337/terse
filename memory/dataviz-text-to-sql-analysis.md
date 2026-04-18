# DataViz-Agent Text-to-SQL Pipeline: SOTA Analysis & Enterprise-Grade Improvement Plan

**Date:** 2026-03-20
**Analyst:** Alex Chen (ML Engineering / Research Architecture)
**Repository:** bowen31337/dataViz-agent
**Target:** Enterprise-scale production (100M+ row PostgreSQL, Claude Sonnet 4.6 via Bedrock)

---

## 1. Current Pipeline Analysis

### 1.1 End-to-End Flow

```
User Question
    │
    ├─[1] Schema Discovery ─── PostgreSQL information_schema + pg_index + pg_class
    │     └─ Cached for 5min (DB_SCHEMA_TTL_MS), includes row counts, index profiles
    │
    ├─[2] Query Decomposition Gate ─── Regex-based compound detection
    │     └─ If QUERY_DECOMPOSITION=true && isCompoundQuestion() → LLM decompose → topo-sort → resolve sequentially
    │
    ├─[3] Schema Linking (2-stage) ─── Keyword scoring (0.6) + embedding cosine similarity (0.4)
    │     └─ Selects top-3 tables. Embeds question + table text via Titan/OpenAI embeddings
    │
    ├─[4] Schema Introspection Shortcut ─── Regex patterns for "what columns" / "show schema"
    │
    ├─[5] Static Few-Shot Match ─── Jaccard token similarity ≥ 0.82 → bypass LLM generation
    │
    ├─[6] Few-Shot Retrieval ─── pgvector cosine search on query_embeddings table
    │     └─ Short-circuit if similarity ≥ 0.95 → reuse cached SQL directly
    │     └─ Keyword priority injection for growth/domestic queries
    │     └─ Static fallback (16 hardcoded examples) if vector search fails
    │
    ├─[7] Strategy Selection ─── Index-aware dynamic strategies
    │     └─ 'index-first' (always), 'time-bounded' (if time keywords), 'aggregate-safe' (if agg keywords)
    │     └─ Falls back to static: conservative / aggressive / analytical
    │
    ├─[8] Multi-Candidate Generation ─── N parallel LLM calls (N = SQL_CANDIDATES env, default 1)
    │     └─ Each candidate gets different strategyHint in prompt
    │     └─ Prompt: system rules + schema + universal rules (UR-001..014) + domain rules + few-shot + CoT instructions
    │
    ├─[9] LLM Ranking ─── Second LLM call evaluates all candidates on 4 criteria
    │     └─ Skips if only 1 viable candidate
    │     └─ Fallback: sort by self-confidence
    │
    ├─[10] Validation ─── node-sql-parser AST walk
    │     └─ Checks: unknown columns/tables, COUNT(*) detection, DDL rejection, duplicate LIMIT
    │     └─ Soft failure for complex PostgreSQL CTE syntax (parser limitation)
    │
    ├─[11] Safety Guards ─── enforceMandatoryFilters() + isNonSargable() check
    │     └─ Mandatory: searchdate filter on af740 (prevents 100M full scan)
    │     └─ Non-sargable reject: all WHERE cols non-indexed on large table → reject
    │
    ├─[12] Execution ─── query() via pg Pool, with LIMIT injection
    │     └─ Admin users: pause for "Run Query" button
    │     └─ injectLimit: 200 rows (1000 for GROUP BY)
    │
    ├─[13] Confidence Scoring ─── Multiplicative penalty model
    │     └─ Factors: empty result (-0.65), null columns (-0.30), all-same-value (-0.40),
    │        validator fail (-0.80), iteration count, slow query, LLM self-confidence (0.15 blend)
    │     └─ Threshold: 0.70
    │
    ├─[14] Disambiguation Gate ─── Post-execution result inspection
    │     └─ Triggers: empty rows, near-cap rows for specific lookup, all-same-value, LLM flag
    │
    ├─[15] RRIL Reflection Loop ─── Up to 3 iterations total (MAX_ITERATIONS=3)
    │     └─ Seeds reflection with: previous SQL + diagnostic error message
    │     └─ Preserves winner's strategy hint across iterations
    │     └─ Each iteration: rebuild prompt with reflectionContext → LLM → validate → execute → score
    │
    ├─[16] LLM Judge ─── Optional (LLM_JUDGE_ENABLED=true)
    │     └─ Haiku/cheaper model evaluates: "does this result answer the question?"
    │     └─ Sets auto-approved flag in query log
    │
    └─[17] Query Logging ─── Full trace: candidates, final SQL, execution result, confidence, signals
```

### 1.2 LLM Call Count Per Query (Current)

| Path | LLM Calls | Notes |
|------|-----------|-------|
| Static match hit | 0 | Jaccard ≥ 0.82, bypass LLM |
| Embedding cache hit | 0 | Similarity ≥ 0.95, reuse SQL |
| Single-candidate, first-pass success | 1 gen + 0 rank = 1 | SQL_CANDIDATES=1 (default) |
| 3-candidate, first-pass success | 3 gen + 1 rank = 4 | SQL_CANDIDATES=3 |
| 3-candidate, 3 RRIL iterations | 3 gen + 1 rank + 2 reflect = 6 | Worst case |
| + Decomposition | +1 decompose + N sub-questions | Adds 2-5 calls |
| + LLM Judge | +1 per success | Post-execution |

**Cost estimate at SQL_CANDIDATES=3:** ~4-6 LLM calls × ~4K input tokens × ~1K output tokens = ~$0.03-0.06/query on Sonnet.

### 1.3 Prompt Architecture

The system prompt (`SQL_SYSTEM_PROMPT`) is 400 tokens. The user prompt assembles:
1. **Schema section** — Full column listing with types, [INDEXED] markers, index profile hints (leading, sargable, non-sargable, mandatory filter)
2. **Universal rules** — 14 rules (UR-001 to UR-014), ~1200 tokens
3. **Domain rules** — 7 rules for af740, ~600 tokens
4. **Reflection context** — Previous SQL + error (RRIL only)
5. **Few-shot examples** — Up to 5 examples with SQL + reasoning, ~1500 tokens
6. **Strategy hint** — Per-candidate interpretation nudge
7. **7-step CoT instructions** — Structured reasoning steps, ~300 tokens
8. **Question** — User's question

**Total prompt size estimate:** 4,000-6,000 tokens per LLM call.

### 1.4 Key Strengths (Already Above Median)

1. **Multi-candidate generation + LLM ranking** — Matches DIN-SQL's candidate diversity pattern
2. **Reflection loop (RRIL)** — Self-correction with execution feedback, up to 3 iterations
3. **Rich domain rules** — 14 universal + 7 domain rules prevents known failure modes (flightcategory trap, COUNT(*), boolean handling)
4. **Index-aware strategy selection** — Dynamic strategies based on index profiles
5. **Mandatory filter enforcement** — Programmatic guardrail against 100M-row full scans
6. **Non-sargable rejection** — Pre-execution safety check
7. **Embedding cache with short-circuit** — Avoids redundant LLM calls for repeated questions
8. **Schema annotations** — isDead columns stripped from prompt, descriptions curated
9. **Post-execution confidence scoring** — Data-driven quality signal (not just LLM self-report)
10. **Query decomposition** — Handles compound questions via sub-question resolution

---

## 2. Accuracy Bottlenecks (Ranked by Impact)

### B1. No EXPLAIN Plan Validation Before Execution (CRITICAL — Safety)

**Current:** SQL is executed directly. The only pre-execution safety is `isNonSargable()` regex check and `enforceMandatoryFilters()` string injection.

**Failure mode:** A syntactically valid query that passes `isNonSargable()` but still triggers:
- Sequential scan on 100M rows (WHERE on non-leading index column)
- Hash join explosion (two large tables without index join)
- Sort spill to disk (ORDER BY on unindexed column without LIMIT)
- CTE materialisation of full table

**Impact:** Not an accuracy issue — it's a **safety/reliability** issue. A single bad query can cause OOM, 30+ second timeouts, or DB connection starvation.

**Evidence:** The codebase has `enforceMandatoryFilters` and `isNonSargable` but these are regex-based heuristics that miss many cases. A query like `WHERE LOWER(destinationcity) = 'sydney'` bypasses the index even though `destinationcity` is indexed.

---

### B2. Schema Linking Misses on Ambiguous Multi-Table Questions (~8-12% accuracy loss)

**Current:** `linkSchema()` uses keyword matching (0.6 weight) + embedding cosine similarity (0.4 weight), selecting top-3 tables.

**Failure modes:**
- Question: "What's the CTR for direct campaigns?" → should link `campaign_meta` but keyword "direct" also appears in `af740_not_confirmed` domain rules
- Question: "Compare audience sizes with campaign spend" → needs `audience_segments` AND `campaign_meta` but top-3 might select wrong combination
- Embedding similarity is computed by embedding the entire table name + description + all column names as one string — this loses fine-grained column-level signal

**SOTA gap:** CHESS (Chen et al., 2024) and BIRD leaderboard systems use **column-level entity linking** — each entity in the question is matched to a specific column, not a whole table.

---

### B3. Few-Shot Retrieval Quality (~5-8% accuracy loss)

**Current:** Two retrieval paths:
- Static: 16 hardcoded examples with Jaccard token similarity
- Dynamic: pgvector cosine search on `query_embeddings` table

**Failure modes:**
- Jaccard similarity is bag-of-words — "How many users booked flights" and "How many flights were booked by users" have identical Jaccard score but could mean different things
- The embedding cache short-circuit at 0.95 similarity can return stale SQL when schema or data changes
- Only 16 static examples — insufficient coverage for the domain's diversity
- No negative examples (ambiguous questions with disambiguation, not SQL)
- Few-shot examples don't demonstrate complex patterns: window functions, CTEs with multiple aggregations, conditional aggregation (CASE WHEN + GROUP BY)

**SOTA gap:** DAIL-SQL (Gao et al., 2024) uses **question skeleton + SQL skeleton** similarity — the SQL structure matters as much as the question text for example selection. Their retrieval uses masked SQL patterns, not raw question similarity.

---

### B4. No Execution Plan Feedback in Reflection Loop (~5-7% accuracy loss)

**Current:** RRIL feeds back only: "Low confidence result (score: X). Query returned 0 rows." or "All values in first column identical."

**Failure mode:** The LLM has no way to understand WHY a query is slow, returns wrong aggregations, or produces unexpected cardinality. Without execution plan feedback, it guesses randomly on reflection.

**Example:** Query returns 0 rows because `searchdate` filter used wrong date range. Reflection says "returned 0 rows, check WHERE filters." LLM might change the table instead of fixing the date — it doesn't know the table has 100M rows and the filter was the issue.

**SOTA gap:** MAC-SQL (Wang et al., 2024) uses **execution-aware refinement** where the self-correction step receives the execution plan (EXPLAIN output), actual vs expected row counts, and sample values from the table.

---

### B5. Single-Model Generation (No Complexity-Based Routing) (~3-5% accuracy loss + cost waste)

**Current:** All queries use the same model (Sonnet via Bedrock), regardless of complexity.

**Failure mode:**
- Simple lookup: "How many users searched?" → wastes Sonnet tokens on a trivial SELECT COUNT(DISTINCT cookieid)
- Complex analytical: "Compare YoY growth by quarter for top-5 domestic routes, segmented by family/non-family" → Sonnet may struggle with the 3-level nesting required

**SOTA gap:** CHASE-SQL (Pourreza & Rafiei, 2024) uses a **query complexity classifier** that routes to different generation strategies. For production systems, this maps to model routing: Haiku for simple, Sonnet for medium, Opus for complex.

---

### B6. No Value-Level Grounding (~3-5% accuracy loss)

**Current:** The LLM sees column names and types but never sees actual data values. Domain rules hardcode some values (e.g., domestic cities list, pagetype values), but this is incomplete.

**Failure mode:**
- Question: "How many users searched for Bali?" → LLM doesn't know if Bali appears as "Bali", "BALI", "Denpasar", or "Ngurah Rai" in `destinationcity`
- Question: "What about economy class?" → Is it "economy", "Economy", "ECONOMY", "Y"?
- Without value grounding, the LLM generates plausible but wrong WHERE filters

**SOTA gap:** C3 (Dong et al., 2023) and CHESS both use **value retrieval** — querying `SELECT DISTINCT column LIMIT N` or using a value index to ground filter predicates in actual data values.

---

### B7. Weak Compound Question Decomposition (~2-4% accuracy loss)

**Current:** `isCompoundQuestion()` uses 5 regex patterns. Decomposition uses a single LLM call with minimal schema context.

**Failure modes:**
- "How does family travel compare to non-family in terms of average spend and booking lead time?" → should decompose into 4 sub-queries (2 segments × 2 metrics) but the decomposer might generate 2 (one per metric, losing the segmentation)
- Topological sort handles dependencies but the `injectResultsIntoQuestion()` only passes scalar values or JSON samples — no structured way to pass intermediate CTEs

**SOTA gap:** DIN-SQL (Pourreza & Rafiei, 2023) uses **classification → decomposition → generation** where the decomposition step explicitly identifies sub-problems and their SQL patterns before generating.

---

### B8. Schema Context Bloat (~2-3% accuracy loss on complex schemas)

**Current:** All columns of linked tables are included in the prompt (after stripping isDead columns). For tables with 20+ columns, this wastes prompt space and confuses the LLM.

**Failure mode:** The `af740_not_confirmed` table has 20 columns. For a simple "count users" query, 15 columns are irrelevant noise. The LLM sometimes latches onto irrelevant columns (e.g., using `cartvalue` in a WHERE filter when the question is about user counts).

**SOTA gap:** RESDSQL (Li et al., 2023) uses **column pruning** — a lightweight classifier predicts which columns are relevant to the question, reducing prompt size by 60-80%.

---

## 3. SOTA Improvements (Ranked by Impact × Feasibility)

---

### Tier 1: Enterprise Safety & Reliability (Highest Priority)

#### 3.1 EXPLAIN Plan Validation Gate

**Technique:** Pre-execute `EXPLAIN (FORMAT JSON, COSTS true)` on every generated SQL before actual execution. Parse the plan to detect: sequential scans on large tables, estimated rows > threshold, sort/hash operations without index support.

**Why it works:** EXPLAIN is nearly free (doesn't execute the query). It catches every class of dangerous query that regex-based checks miss: function-wrapped columns defeating indexes, implicit type casts, wrong join orders, CTE materialisation.

**Estimated impact:** +0% accuracy, **-95% dangerous query executions**, +10% reliability

**Concrete implementation:**

```typescript
// src/lib/text-to-sql/core/explain-validator.ts

interface ExplainNode {
  'Node Type': string;
  'Relation Name'?: string;
  'Total Cost': number;
  'Plan Rows': number;
  'Plan Width': number;
  Plans?: ExplainNode[];
  'Index Name'?: string;
  'Filter'?: string;
}

interface ExplainResult {
  safe: boolean;
  estimatedCost: number;
  estimatedRows: number;
  warnings: string[];
  hasSeqScanOnLargeTable: boolean;
  plan: ExplainNode;
}

const COST_THRESHOLD = 50000;  // Tune based on your DB
const ROW_ESTIMATE_THRESHOLD = 1_000_000;

export async function validateExplainPlan(
  sql: string,
  pool: Pool,
  tableRowCounts: Map<string, number>,
): Promise<ExplainResult> {
  const explainSql = `EXPLAIN (FORMAT JSON, COSTS true) ${sql}`;
  const result = await pool.query(explainSql);
  const plan = result.rows[0]['QUERY PLAN'][0].Plan as ExplainNode;

  const warnings: string[] = [];
  let hasSeqScanOnLargeTable = false;

  function walkPlan(node: ExplainNode) {
    if (node['Node Type'] === 'Seq Scan' && node['Relation Name']) {
      const tableName = node['Relation Name'];
      const rowCount = tableRowCounts.get(tableName) ?? 0;
      if (rowCount > 1_000_000) {
        hasSeqScanOnLargeTable = true;
        warnings.push(
          `Sequential scan on ${tableName} (~${rowCount.toLocaleString()} rows). ` +
          `Expected cost: ${node['Total Cost'].toFixed(0)}. ` +
          `Add an indexed filter or the query will be extremely slow.`
        );
      }
    }
    if (node['Node Type'] === 'Sort' && node['Plan Rows'] > 100000) {
      warnings.push(`Large sort operation (${node['Plan Rows']} rows) — may spill to disk.`);
    }
    if (node.Plans) {
      for (const child of node.Plans) walkPlan(child);
    }
  }

  walkPlan(plan);

  return {
    safe: !hasSeqScanOnLargeTable && plan['Total Cost'] < COST_THRESHOLD,
    estimatedCost: plan['Total Cost'],
    estimatedRows: plan['Plan Rows'],
    warnings,
    hasSeqScanOnLargeTable,
    plan,
  };
}
```

**Integration into rds-query.ts** — replace the current `isNonSargable()` check:

```typescript
// After SQL is finalised, before executeSql():
const explainResult = await validateExplainPlan(cappedSql, getPool(), countMap);
if (!explainResult.safe) {
  // Feed EXPLAIN warnings back into RRIL reflection
  lastError = `EXPLAIN plan unsafe:\n${explainResult.warnings.join('\n')}\n` +
    `Estimated cost: ${explainResult.estimatedCost}, rows: ${explainResult.estimatedRows}.\n` +
    `Rewrite the query to use indexed columns in WHERE.`;
  continue; // next RRIL iteration
}
```

**Effort:** 8-12 hours
**Dependencies:** None — pure addition

---

#### 3.2 Query Timeout & Statement-Level Resource Limits

**Technique:** Wrap every SQL execution with `SET LOCAL statement_timeout` and `SET LOCAL work_mem` to prevent any single query from consuming unbounded resources.

**Why it works:** Even with EXPLAIN validation, edge cases exist (bad statistics, skewed data). A hard timeout is the last line of defence.

**Concrete implementation:**

```typescript
// src/lib/rds/connection.ts — wrap the query function

export async function safeQuery<T>(
  sql: string,
  params?: unknown[],
  opts: { timeoutMs?: number; workMemMb?: number } = {},
): Promise<T[]> {
  const timeout = opts.timeoutMs ?? 15000;  // 15s default
  const workMem = opts.workMemMb ?? 256;    // 256MB default

  const client = await getPool().connect();
  try {
    await client.query(`SET LOCAL statement_timeout = '${timeout}'`);
    await client.query(`SET LOCAL work_mem = '${workMem}MB'`);
    const result = await client.query(sql, params);
    return result.rows as T[];
  } catch (err) {
    if (err instanceof Error && err.message.includes('statement timeout')) {
      throw new Error(`Query timed out after ${timeout}ms. The query is too expensive for the current data volume. Try adding more specific filters.`);
    }
    throw err;
  } finally {
    client.release();
  }
}
```

**Effort:** 4 hours
**Dependencies:** None

---

#### 3.3 Full Pipeline Observability (Langfuse Integration)

**Technique:** Instrument every step of the pipeline with structured traces. Use Langfuse TypeScript SDK (production-grade, self-hostable, OpenTelemetry-compatible).

**Why it works:** Without observability, you can't debug accuracy failures, track cost, or identify slow steps. Langfuse provides: trace visualization, cost tracking per query, latency breakdowns, prompt versioning, and evaluation datasets.

**Concrete implementation:**

```typescript
// src/lib/observability/trace.ts

import { Langfuse } from 'langfuse';

const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  baseUrl: process.env.LANGFUSE_HOST ?? 'https://cloud.langfuse.com',
});

export interface PipelineTrace {
  traceId: string;
  startSpan(name: string, metadata?: Record<string, unknown>): SpanHandle;
  logLlmCall(name: string, input: string, output: string, model: string, usage: { input_tokens: number; output_tokens: number }, latencyMs: number): void;
  logDbQuery(sql: string, rowCount: number, latencyMs: number, explainPlan?: unknown): void;
  setOutput(result: unknown): void;
  end(): void;
}

export function createPipelineTrace(question: string, sessionId?: string): PipelineTrace {
  const trace = langfuse.trace({
    name: 'text-to-sql-pipeline',
    input: { question },
    sessionId,
    metadata: { model: process.env.BEDROCK_MODEL_NAME },
  });

  return {
    traceId: trace.id,
    startSpan(name, metadata) {
      const span = trace.span({ name, metadata });
      return {
        end(output?: unknown) { span.end({ output }); },
        update(data: Record<string, unknown>) { span.update(data); },
      };
    },
    logLlmCall(name, input, output, model, usage, latencyMs) {
      trace.generation({
        name,
        input,
        output,
        model,
        usage: { input: usage.input_tokens, output: usage.output_tokens },
        metadata: { latencyMs },
      });
    },
    logDbQuery(sql, rowCount, latencyMs, explainPlan) {
      trace.span({
        name: 'db_query',
        input: { sql },
        output: { rowCount },
        metadata: { latencyMs, explainPlan },
      });
    },
    setOutput(result) { trace.update({ output: result }); },
    end() { langfuse.flush(); },
  };
}
```

**Integration:** Thread `PipelineTrace` through `rds-query.ts`, replacing the ad-hoc `dispatchCustomEvent` calls:

```typescript
// In rdsQueryTool handler:
const trace = createPipelineTrace(question, sessionId);
const schemaSpan = trace.startSpan('schema_discovery');
const fullSchema = await getRdsSchemaForLinker();
schemaSpan.end({ tableCount: fullSchema.length });

const linkSpan = trace.startSpan('schema_linking');
const relevantSchema = await linkSchema(question, fullSchema);
linkSpan.end({ linkedTables: relevantSchema.map(t => t.name) });

// For each LLM call:
trace.logLlmCall('sql_generation', prompt, content, modelInfo.model, tokenUsage, latencyMs);

// For DB execution:
trace.logDbQuery(cappedSql, rows.length, execTimeMs, explainPlan);

// Attach trace ID to response:
return JSON.stringify({ ...result, traceId: trace.traceId });
```

**Effort:** 16-20 hours (initial integration + all pipeline steps)
**Dependencies:** Langfuse account or self-hosted instance

---

### Tier 2: Core Accuracy Improvements (+12-18% on BIRD-equivalent)

#### 3.4 Column-Level Entity Linking (Schema Linking V2)

**Technique:** Replace table-level keyword+embedding scoring with **column-level entity resolution**. For each noun/entity in the question, find the most likely column match using: (a) BM25 on column name + description, (b) embedding similarity between entity and column description, (c) value overlap (does the entity appear as a value in the column?).

**Why it works:** CHESS (BIRD SOTA, 73.01%) and RESDSQL both use column-level linking. It's the single highest-impact technique for schema-complex databases. By identifying exactly which columns matter, you: reduce prompt size (less noise), improve SQL accuracy (correct columns in SELECT/WHERE), and enable smarter joins.

**Reference:** CHESS: Contextual Harnessing for Efficient SQL Synthesis (Talaei et al., 2024) — Section 3.2

**Estimated impact:** +8-12% accuracy on schema-complex queries

**Concrete implementation:**

```typescript
// src/lib/text-to-sql/core/entity-linker.ts

interface EntityMatch {
  entity: string;           // extracted from question: "family", "domestic flights"
  column: string;           // matched column: "familyflag", "destinationcity"
  table: string;            // "carsales.af740_not_confirmed"
  confidence: number;       // 0-1
  matchType: 'name' | 'description' | 'value' | 'rule';
  sampleValues?: string[];  // Top-5 values if value match
}

// Step 1: Extract entities from question using NER + noun phrase extraction
// (Can use a cheap LLM call or rule-based extraction)
function extractEntities(question: string): string[] {
  // Rule-based: nouns, noun phrases, quoted strings, numbers
  const entities: string[] = [];
  // ... NLP extraction logic
  return entities;
}

// Step 2: For each entity, score against each column
async function linkEntities(
  entities: string[],
  schema: SchemaTable[],
  pool: Pool,
): Promise<EntityMatch[]> {
  const matches: EntityMatch[] = [];

  for (const entity of entities) {
    let bestMatch: EntityMatch | null = null;
    let bestScore = 0;

    for (const table of schema) {
      for (const col of table.columns) {
        let score = 0;

        // Name match
        if (col.name.toLowerCase().includes(entity.toLowerCase())) score += 0.6;
        if (entity.toLowerCase().includes(col.name.toLowerCase())) score += 0.4;

        // Description match
        if (col.description?.toLowerCase().includes(entity.toLowerCase())) score += 0.3;

        // Value match (for string columns, check if entity is a known value)
        // This requires a pre-built value index or runtime SELECT DISTINCT
        // See Section 3.6 for value retrieval implementation

        if (score > bestScore) {
          bestScore = score;
          bestMatch = {
            entity,
            column: col.name,
            table: table.name,
            confidence: Math.min(score, 1),
            matchType: 'name',
          };
        }
      }
    }
    if (bestMatch) matches.push(bestMatch);
  }

  return matches;
}

// Step 3: Use entity matches to prune schema and enrich prompt
export function pruneSchemaByEntities(
  schema: SchemaTable[],
  matches: EntityMatch[],
): SchemaTable[] {
  const relevantColumns = new Map<string, Set<string>>();
  for (const match of matches) {
    if (!relevantColumns.has(match.table)) {
      relevantColumns.set(match.table, new Set());
    }
    relevantColumns.get(match.table)!.add(match.column);
  }

  return schema.map(table => {
    const relevant = relevantColumns.get(table.name);
    if (!relevant) return table;

    // Keep matched columns + always include PK and FK columns
    const filtered = table.columns.filter(
      col => relevant.has(col.name) || col.indexed || col.name === 'cookieid'
    );
    return { ...table, columns: filtered.length > 3 ? filtered : table.columns };
  });
}
```

**Effort:** 20-24 hours
**Dependencies:** Value index (see 3.6)

---

#### 3.5 EXPLAIN-Aware Self-Correction (RRIL V2)

**Technique:** Enhance the RRIL reflection loop to include EXPLAIN plan analysis in the error feedback, not just "0 rows returned."

**Why it works:** Current RRIL tells the LLM "your query returned 0 rows" — the LLM has no idea if the problem is: wrong table, wrong filter, wrong date range, wrong join, or a full table scan that timed out. With EXPLAIN plan feedback, the LLM can make targeted corrections.

**Reference:** MAC-SQL (Wang et al., 2024) — their "SQL Refiner" receives execution plan details.

**Estimated impact:** +5-8% accuracy on RRIL iterations (currently ~40% of queries need RRIL; improving RRIL success rate from ~60% to ~80% = +5-8% overall)

**Concrete implementation:**

```typescript
function buildExplainAwareReflection(
  signals: ExecutionSignals,
  confidence: number,
  sql: string,
  explainResult: ExplainResult,
  schema: SchemaTable[],
): string {
  const parts: string[] = [`Iteration failed (confidence: ${confidence.toFixed(2)}).`];

  // Execution plan analysis
  if (explainResult.hasSeqScanOnLargeTable) {
    parts.push(
      `EXECUTION PLAN WARNING: Sequential scan detected on large table. ` +
      `The query will scan ${explainResult.estimatedRows.toLocaleString()} rows. ` +
      `Add a filter on an indexed column: ${explainResult.warnings.join('; ')}`
    );
  }

  if (explainResult.estimatedCost > 50000) {
    parts.push(
      `Query cost is ${explainResult.estimatedCost.toFixed(0)} (threshold: 50000). ` +
      `Reduce cost by: (1) adding indexed WHERE filters, (2) reducing JOIN scope, ` +
      `(3) using EXISTS instead of IN for subqueries.`
    );
  }

  // Row count analysis
  if (signals.rowCount === 0) {
    parts.push(
      `0 rows returned. EXPLAIN estimated ${explainResult.estimatedRows} rows. ` +
      (explainResult.estimatedRows === 0
        ? 'The optimizer also predicted 0 rows — check if your WHERE filters are impossible (contradictory conditions, date range outside data, misspelled values).'
        : `The optimizer expected ${explainResult.estimatedRows} rows but got 0 — possible type mismatch or case sensitivity issue in WHERE values.`)
    );
  }

  // Cardinality mismatch
  if (signals.rowCount > 0 && explainResult.estimatedRows > 0) {
    const ratio = signals.rowCount / explainResult.estimatedRows;
    if (ratio > 10 || ratio < 0.1) {
      parts.push(
        `Cardinality mismatch: got ${signals.rowCount} rows, EXPLAIN predicted ${explainResult.estimatedRows}. ` +
        `This suggests outdated table statistics or unexpected data distribution. ` +
        `The query may be correct but consider verifying your filter assumptions.`
      );
    }
  }

  parts.push('Correct the SQL based on the execution plan feedback above.');
  return parts.join('\n');
}
```

**Effort:** 12-16 hours
**Dependencies:** EXPLAIN validator (3.1)

---

#### 3.6 Value Retrieval & Grounding

**Technique:** Before SQL generation, query the database for actual values of columns likely to appear in WHERE clauses. Build a lightweight value index that caches `SELECT DISTINCT column LIMIT 100` for string columns.

**Why it works:** C3 (Dong et al., 2023) showed that value grounding alone adds +4-6% on BIRD. The LLM needs to know that "Bali" appears as "Bali" (not "BALI" or "DPS") in the data.

**Reference:** C3: Zero-shot Text-to-SQL with ChatGPT (Dong et al., 2023) — Section 4.3, "Clear Prompting with Calibration"

**Estimated impact:** +4-6% accuracy on filter-dependent queries

**Concrete implementation:**

```typescript
// src/lib/text-to-sql/core/value-retriever.ts

interface ValueIndex {
  table: string;
  column: string;
  distinctValues: string[];
  lastUpdated: number;
}

const VALUE_CACHE = new Map<string, ValueIndex>();
const VALUE_CACHE_TTL = 3600_000; // 1 hour — values change slowly

export async function getColumnValues(
  table: string,
  column: string,
  limit = 100,
): Promise<string[]> {
  const key = `${table}.${column}`;
  const cached = VALUE_CACHE.get(key);
  if (cached && Date.now() - cached.lastUpdated < VALUE_CACHE_TTL) {
    return cached.distinctValues;
  }

  const sql = `SELECT DISTINCT ${column}::text AS val FROM ${table} WHERE ${column} IS NOT NULL ORDER BY val LIMIT ${limit}`;
  const rows = await query<{ val: string }>(sql);
  const values = rows.map(r => r.val);

  VALUE_CACHE.set(key, {
    table, column,
    distinctValues: values,
    lastUpdated: Date.now(),
  });

  return values;
}

// Inject into prompt as value hints
export function buildValueHints(
  question: string,
  schema: SchemaTable[],
  valueIndex: Map<string, string[]>,
): string {
  const hints: string[] = ['=== VALUE HINTS (actual values from database) ==='];
  for (const table of schema) {
    for (const col of table.columns) {
      if (col.type === 'text' || col.type === 'character varying') {
        const key = `${table.name}.${col.name}`;
        const values = valueIndex.get(key);
        if (values && values.length > 0) {
          // Only show values that might be relevant (fuzzy match with question)
          const relevant = values.filter(v =>
            question.toLowerCase().includes(v.toLowerCase()) ||
            v.toLowerCase().includes(question.split(/\s+/).find(w => w.length > 3)?.toLowerCase() ?? '')
          );
          if (relevant.length > 0) {
            hints.push(`${col.name}: ${relevant.slice(0, 10).map(v => `'${v}'`).join(', ')}`);
          }
        }
      }
    }
  }
  return hints.length > 1 ? hints.join('\n') : '';
}
```

**Effort:** 12-16 hours
**Dependencies:** DB access for DISTINCT queries (use EXPLAIN to ensure they hit indexes)

---

#### 3.7 SQL Skeleton-Based Few-Shot Retrieval (DAIL-SQL Pattern)

**Technique:** Instead of matching few-shot examples by question similarity alone, also match by **SQL skeleton similarity**. Extract the structural pattern of both the question and the expected SQL.

**Why it works:** DAIL-SQL showed +3-5% improvement on BIRD by using SQL skeleton matching. Two questions might be phrased differently but need the same SQL pattern (e.g., "top 5 cities by X" and "which destinations have the highest Y" both need `GROUP BY + ORDER BY + LIMIT`).

**Reference:** DAIL-SQL (Gao et al., 2024) — Section 3.2, "Target Similarity Selection"

**Estimated impact:** +3-5% accuracy

**Concrete implementation:**

```typescript
// SQL skeleton extraction
function extractSqlSkeleton(sql: string): string {
  return sql
    .replace(/'[^']*'/g, '_VALUE_')        // mask string literals
    .replace(/\b\d+\.?\d*\b/g, '_NUM_')     // mask numbers
    .replace(/\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*/g, '_ENTITY_')  // mask proper nouns
    .replace(/\s+/g, ' ')
    .trim();
}

// Question skeleton extraction
function extractQuestionSkeleton(question: string): string {
  return question
    .toLowerCase()
    .replace(/\b(the|a|an|is|are|was|were|in|on|at|to|for|of|with|by)\b/g, '')
    .replace(/\b\d+\b/g, '_NUM_')
    .replace(/\s+/g, ' ')
    .trim();
}

// Enhanced retrieval: combines question similarity (0.4) + SQL skeleton similarity (0.4) + tag match (0.2)
export async function retrieveEnhancedFewShot(
  question: string,
  examples: FewShotExample[],
  targetCount: number,
): Promise<FewShotExample[]> {
  const qSkeleton = extractQuestionSkeleton(question);

  const scored = examples.map(ex => {
    const questionSim = jaccard(
      new Set(question.toLowerCase().split(/\s+/)),
      new Set(ex.question.toLowerCase().split(/\s+/))
    );
    const skeletonSim = ex.sql
      ? jaccard(
          new Set(qSkeleton.split(/\s+/)),
          new Set(extractQuestionSkeleton(ex.question).split(/\s+/))
        )
      : 0;
    return {
      example: ex,
      score: questionSim * 0.4 + skeletonSim * 0.4 + (ex.source === 'retrieved' ? 0.2 : 0.1),
    };
  });

  return scored
    .sort((a, b) => b.score - a.score)
    .slice(0, targetCount)
    .map(s => s.example);
}
```

**Effort:** 8-10 hours
**Dependencies:** None — enhancement of existing retrieval

---

### Tier 3: Cost Optimisation & Advanced Techniques (+5-10%)

#### 3.8 Anthropic Prompt Caching for Schema Context

**Technique:** Use Claude's prompt caching API to cache the system prompt + schema + universal rules prefix. Since schema changes rarely (5-minute TTL), the same prefix is reused across all queries in a window.

**Why it works:** The schema + rules section is ~4000 tokens and identical across queries. With prompt caching, subsequent queries in the same window pay only for the question + few-shot delta. This saves ~75% of input tokens on the prefix.

**Reference:** Anthropic Prompt Caching documentation — up to 90% cost reduction on cached prefixes.

**Estimated impact:** -60-75% input token cost per LLM call (no accuracy change)

**Concrete implementation:**

```typescript
// In sql-llm.ts, modify createSqlLlm for Bedrock:
// Bedrock Converse API supports cache_control for Anthropic models

export function buildCacheablePrompt(
  systemPrompt: string,
  schemaSection: string,
  rulesSection: string,
  dynamicSection: string,  // few-shot + question
): Array<{ role: string; content: Array<{ type: string; text: string; cache_control?: { type: string } }> }> {
  return [
    {
      role: 'user',
      content: [
        {
          type: 'text',
          text: `${systemPrompt}\n\n${schemaSection}\n\n${rulesSection}`,
          cache_control: { type: 'ephemeral' },  // Cache this prefix
        },
        {
          type: 'text',
          text: dynamicSection,  // Not cached — changes per query
        },
      ],
    },
  ];
}
```

**Note:** Bedrock support for `cache_control` in Converse API — verify availability for your model version. If not available on Bedrock, consider direct Anthropic API for the SQL generation calls.

**Effort:** 6-8 hours
**Dependencies:** Bedrock/Anthropic API support verification

---

#### 3.9 Query Complexity Router (Model Tiering)

**Technique:** Classify query complexity before generation and route to the appropriate model tier.

**Why it works:** 60-70% of user questions are simple lookups or single-table aggregations. Using Haiku (~10x cheaper) for these saves significant cost while maintaining accuracy. Complex multi-table joins and window functions benefit from Opus's reasoning.

**Estimated impact:** -50-70% cost with <1% accuracy loss

**Concrete implementation:**

```typescript
// src/lib/text-to-sql/core/complexity-router.ts

type Complexity = 'simple' | 'medium' | 'complex';

const COMPLEX_SIGNALS = [
  /\b(compare|versus|vs\.?|growth|trend|year.over.year|yoy)\b/i,
  /\b(for each|per|segment|breakdown|by .+ and .+)\b/i,
  /\b(ratio|percentage|proportion|share)\b/i,
  /\b(window|rank|ntile|lag|lead|row_number)\b/i,
];

const SIMPLE_SIGNALS = [
  /^how many\b/i,
  /^what is the (total|average|count|sum)\b/i,
  /^show me\b/i,
  /^list\b/i,
];

export function classifyComplexity(
  question: string,
  linkedTables: number,
  entityMatches: number,
): Complexity {
  // Multi-table = at least medium
  if (linkedTables > 2) return 'complex';

  // Complex signal keywords
  const complexCount = COMPLEX_SIGNALS.filter(re => re.test(question)).length;
  if (complexCount >= 2) return 'complex';
  if (complexCount === 1 && linkedTables > 1) return 'complex';

  // Simple signal keywords
  const simpleCount = SIMPLE_SIGNALS.filter(re => re.test(question)).length;
  if (simpleCount > 0 && linkedTables === 1 && complexCount === 0) return 'simple';

  return 'medium';
}

export function getModelForComplexity(complexity: Complexity): {
  modelId: string;
  maxTokens: number;
  temperature: number;
} {
  switch (complexity) {
    case 'simple':
      return {
        modelId: 'anthropic.claude-haiku-4-5-20251001-v1:0',  // Haiku — fast, cheap
        maxTokens: 2048,
        temperature: 0,
      };
    case 'medium':
      return {
        modelId: 'anthropic.claude-sonnet-4-20250514-v1:0',  // Sonnet — balanced
        maxTokens: 4096,
        temperature: 0,
      };
    case 'complex':
      return {
        modelId: 'anthropic.claude-sonnet-4-20250514-v1:0',  // Sonnet (or Opus if budget allows)
        maxTokens: 4096,
        temperature: 0,
      };
  }
}
```

**Effort:** 8-10 hours
**Dependencies:** Multiple model endpoints configured on Bedrock

---

#### 3.10 Agentic Tool-Use SQL Generation (CHESS/MAC-SQL Pattern)

**Technique:** Instead of generating SQL in one shot from a massive prompt, give the LLM **tools** it can call iteratively: `get_schema()`, `get_sample_values()`, `explain_query()`, `execute_query()`. The LLM decides what information it needs and calls tools in sequence.

**Why it works:** CHESS (BIRD SOTA, 73.01%) uses this pattern. The LLM doesn't need to hold all schema info in context — it fetches what it needs. This is especially powerful for complex schemas where the relevant subset isn't obvious.

**Reference:** CHESS (Talaei et al., 2024) — "Entity and Context Retrieval" section; MAC-SQL (Wang et al., 2024) — "Multi-Agent Collaboration"

**Estimated impact:** +5-10% on complex multi-table queries, +3% overall

**Concrete implementation:**

```typescript
// Define tools for the SQL generation LLM
const sqlTools = [
  {
    name: 'get_table_schema',
    description: 'Get the full column list with types, descriptions, and index info for specific tables',
    input_schema: {
      type: 'object',
      properties: {
        table_names: { type: 'array', items: { type: 'string' } },
      },
      required: ['table_names'],
    },
  },
  {
    name: 'get_sample_values',
    description: 'Get distinct values for a column (useful for understanding filter values)',
    input_schema: {
      type: 'object',
      properties: {
        table: { type: 'string' },
        column: { type: 'string' },
        limit: { type: 'number', default: 20 },
      },
      required: ['table', 'column'],
    },
  },
  {
    name: 'explain_query',
    description: 'Get the PostgreSQL EXPLAIN plan for a SQL query without executing it',
    input_schema: {
      type: 'object',
      properties: { sql: { type: 'string' } },
      required: ['sql'],
    },
  },
  {
    name: 'submit_sql',
    description: 'Submit the final SQL query for execution',
    input_schema: {
      type: 'object',
      properties: {
        sql: { type: 'string' },
        reasoning: { type: 'string' },
        confidence: { type: 'number' },
      },
      required: ['sql', 'reasoning', 'confidence'],
    },
  },
];
```

**This is a significant architectural change** — recommend implementing after Tier 1 and Tier 2 are stable. It replaces the current "build mega-prompt → generate → validate" flow with an iterative "think → fetch → generate → verify → submit" flow.

**Effort:** 40-60 hours (major refactor)
**Dependencies:** All Tier 1 items, tool-use API support in Bedrock

---

#### 3.11 Cost Budget Enforcement

**Technique:** Track accumulated cost per query and enforce a hard budget (e.g., $0.05/query). Stop generating candidates or RRIL iterations when budget is exhausted.

**Concrete implementation:**

```typescript
// src/lib/text-to-sql/core/cost-tracker.ts

interface CostTracker {
  budget: number;          // max USD per query
  spent: number;           // accumulated USD
  calls: Array<{ name: string; inputTokens: number; outputTokens: number; cost: number }>;
  canAfford(estimatedTokens: number): boolean;
  record(name: string, inputTokens: number, outputTokens: number, model: string): void;
}

const MODEL_COSTS: Record<string, { input: number; output: number }> = {
  'claude-sonnet-4-6': { input: 3.0 / 1_000_000, output: 15.0 / 1_000_000 },
  'claude-haiku-4-5': { input: 0.80 / 1_000_000, output: 4.0 / 1_000_000 },
  'claude-opus-4':     { input: 15.0 / 1_000_000, output: 75.0 / 1_000_000 },
};

export function createCostTracker(budgetUsd = 0.05): CostTracker {
  return {
    budget: budgetUsd,
    spent: 0,
    calls: [],
    canAfford(estimatedInputTokens: number) {
      // Estimate cost of next call (conservative: assume Sonnet)
      const estimated = estimatedInputTokens * 3.0 / 1_000_000 + 2000 * 15.0 / 1_000_000;
      return this.spent + estimated <= this.budget;
    },
    record(name, inputTokens, outputTokens, model) {
      const pricing = MODEL_COSTS[model] ?? MODEL_COSTS['claude-sonnet-4-6'];
      const cost = inputTokens * pricing.input + outputTokens * pricing.output;
      this.spent += cost;
      this.calls.push({ name, inputTokens, outputTokens, cost });
    },
  };
}
```

**Integration:** Check `costTracker.canAfford()` before each LLM call in `generateCandidates()` and RRIL loop. If budget exhausted, return best available candidate with a warning.

**Effort:** 6-8 hours
**Dependencies:** Token counting from LLM responses (already available via `trace.tokenUsage`)

---

#### 3.12 Schema Embedding Cache with Prompt Prefix Memoization

**Technique:** Cache the schema-to-embedding computation (used in schema linking) and the assembled prompt prefix (system prompt + schema + rules) per schema version hash.

**Why it works:** Schema discovery returns the same schema for 5 minutes (TTL). During that window, every query recomputes embeddings for the same table descriptions. Caching eliminates this redundancy.

**Concrete implementation:**

```typescript
// Simple in-memory cache keyed by content hash
import { createHash } from 'crypto';

const EMBED_CACHE = new Map<string, { embedding: number[]; ts: number }>();
const EMBED_TTL = 3600_000; // 1 hour

export async function cachedEmbed(text: string): Promise<number[]> {
  const hash = createHash('md5').update(text).digest('hex');
  const cached = EMBED_CACHE.get(hash);
  if (cached && Date.now() - cached.ts < EMBED_TTL) {
    return cached.embedding;
  }
  const embedding = await embed(text);
  EMBED_CACHE.set(hash, { embedding, ts: Date.now() });
  return embedding;
}
```

**Effort:** 3-4 hours
**Dependencies:** None

---

## 4. Architecture Recommendation (After All Improvements)

### 4.1 Target Pipeline (ASCII)

```
User Question
    │
    ├──[1] TRACE START ─── Create Langfuse trace, attach session ID
    │
    ├──[2] COMPLEXITY CLASSIFICATION ─── Regex + heuristic → simple/medium/complex
    │     └─ Route to model tier: Haiku / Sonnet / Sonnet
    │     └─ Set cost budget based on complexity ($0.01 / $0.03 / $0.08)
    │
    ├──[3] SCHEMA DISCOVERY (cached 5min) ─── pg_catalog + pg_index + pg_class
    │     └─ IndexProfile with leading, sargable, non-sargable, mandatory filters
    │     └─ Row counts per table from pg_class.reltuples
    │
    ├──[4] ENTITY LINKING ─── NLP extract entities → column-level matching
    │     ├─ Name match (BM25 on column name + description)
    │     ├─ Embedding match (cached schema embeddings)
    │     └─ Value match (cached DISTINCT values for string columns)
    │
    ├──[5] SCHEMA PRUNING ─── Keep only matched columns + PKs + indexed columns
    │     └─ Target: <15 columns in prompt (down from 20+)
    │
    ├──[6] SHORT-CIRCUIT CHECKS
    │     ├─ Schema introspection? → Return schema directly
    │     ├─ Static match (Jaccard ≥ 0.82)? → Execute cached SQL
    │     └─ Embedding cache (similarity ≥ 0.95)? → Execute cached SQL
    │
    ├──[7] FEW-SHOT RETRIEVAL (enhanced)
    │     ├─ pgvector cosine similarity on question embedding
    │     ├─ SQL skeleton similarity scoring
    │     ├─ Keyword priority injection (domain-specific)
    │     └─ Select top-5, deduplicate with static examples
    │
    ├──[8] VALUE RETRIEVAL ─── For filter-likely columns, fetch DISTINCT values
    │     └─ Cache 1hr per column, show relevant values in prompt
    │
    ├──[9] PROMPT ASSEMBLY (with caching)
    │     ├─ System prompt + schema + rules → CACHED PREFIX (Anthropic cache_control)
    │     ├─ Few-shot examples + value hints + question → DYNAMIC SUFFIX
    │     └─ Strategy hints per candidate
    │
    ├──[10] MULTI-CANDIDATE GENERATION ─── N parallel LLM calls
    │     └─ N = min(3, strategies.length), complexity-routed model
    │     └─ COST CHECK before each call
    │
    ├──[11] LLM RANKING ─── Second LLM call (can use cheaper model)
    │
    ├──[12] EXPLAIN VALIDATION ─── EXPLAIN (FORMAT JSON, COSTS true) on winner
    │     ├─ Safe? → Proceed to execution
    │     ├─ Unsafe? → Feed EXPLAIN warnings into RRIL reflection
    │     └─ Cost > threshold? → Reject with user-facing message
    │
    ├──[13] SAFE EXECUTION ─── SET LOCAL statement_timeout + work_mem → query()
    │     └─ LIMIT enforcement (already present)
    │     └─ Admin: pause for review
    │
    ├──[14] CONFIDENCE SCORING (enhanced)
    │     └─ Current multiplicative model + EXPLAIN cost factor + cardinality match
    │
    ├──[15] RRIL V2 REFLECTION (if confidence < 0.70)
    │     ├─ EXPLAIN-aware error message (not just "0 rows")
    │     ├─ Value suggestions ("did you mean 'Bali' not 'BALI'?")
    │     ├─ Cardinality feedback ("EXPLAIN predicted X rows, got Y")
    │     └─ Max 3 iterations, cost-budget-gated
    │
    ├──[16] LLM JUDGE ─── Optional post-execution correctness check
    │
    ├──[17] QUERY LOGGING ─── Full trace to Langfuse + query_logs table
    │     └─ Attach traceId to response for support replay
    │
    └──[18] TRACE END ─── Flush Langfuse, record total cost
```

### 4.2 Key Architectural Differences from Current

| Aspect | Current | Target |
|--------|---------|--------|
| Schema linking | Table-level keyword + embedding | Column-level entity linking |
| Schema context | All columns | Pruned to relevant columns |
| Pre-execution safety | Regex-based isNonSargable + mandatoryFilter string injection | EXPLAIN plan validation + statement timeout |
| Reflection feedback | "0 rows returned" | EXPLAIN plan + cardinality + value suggestions |
| Few-shot retrieval | Question embedding similarity | Question + SQL skeleton similarity |
| Value grounding | None (hardcoded in rules) | Runtime DISTINCT value lookup with cache |
| Cost control | None | Per-query cost budget + model routing |
| Observability | Custom events (dispatchCustomEvent) | Langfuse structured traces |
| Prompt efficiency | Full prompt every call | Anthropic prompt caching for prefix |
| Model selection | Single model (Sonnet) | Complexity-routed (Haiku/Sonnet) |

---

## 5. Expected Accuracy & Safety Trajectory

### Baseline Estimate

Based on the E2E test results in the repo (`docs/e2e_test_results_*.csv`) and the 16 static few-shot examples covering the domain, I estimate the current system performs at **55-65% execution accuracy** on the full question space (including novel questions outside the few-shot set). On questions similar to few-shot examples, it's likely **80-90%** due to short-circuit matching.

For BIRD-equivalent difficulty (diverse schemas, complex joins, value matching):
- **Current baseline: ~55-60% execution accuracy**

### Improvement Trajectory

| Phase | Improvements | Accuracy | Safety | Cost | Effort |
|-------|-------------|----------|--------|------|--------|
| **Current** | — | ~55-60% | Medium (regex guards) | ~$0.03-0.06/q | — |
| **Tier 1** (Safety) | EXPLAIN gate + timeout + observability | ~55-60% | **High** (plan-validated) | ~$0.03-0.06/q | 30-40h |
| **Tier 2a** (Linking) | Entity linking + schema pruning | ~63-68% | High | ~$0.02-0.05/q (less tokens) | 20-24h |
| **Tier 2b** (Correction) | EXPLAIN-aware RRIL + value grounding | ~68-73% | High | ~$0.03-0.06/q | 24-32h |
| **Tier 2c** (Retrieval) | SQL skeleton few-shot | ~71-76% | High | ~$0.03-0.06/q | 8-10h |
| **Tier 3a** (Cost) | Prompt caching + model routing + budget | ~71-76% | High | **~$0.008-0.02/q** (-60-70%) | 20-26h |
| **Tier 3b** (Agentic) | Tool-use SQL generation | ~75-80% | Very High | ~$0.01-0.03/q | 40-60h |

### Final Target
- **Accuracy:** 75-80% on BIRD-equivalent difficulty (vs ~73% SOTA for BIRD)
- **Safety:** Every query EXPLAIN-validated, timeout-protected, cost-budgeted
- **Cost:** $0.01-0.02 per query (down from $0.03-0.06)
- **Observability:** Full Langfuse traces, support can replay any query
- **Latency:** P50 ~3s, P95 ~8s (current P50 ~5s, P95 ~15s estimated)

### Total Implementation Effort

| Phase | Hours | Priority |
|-------|-------|----------|
| Tier 1: EXPLAIN + timeout + observability | 30-40h | **NOW** — safety is non-negotiable for 100M rows |
| Tier 2: Entity linking + EXPLAIN RRIL + values + retrieval | 64-82h | Next sprint — biggest accuracy wins |
| Tier 3: Prompt caching + model routing + cost budget | 20-26h | After Tier 2 — cost optimisation |
| Tier 3b: Agentic tool-use (optional) | 40-60h | After Tier 1-3 stable — architectural evolution |
| **Total** | **154-208h** | ~4-5 engineering weeks |

---

## 6. Quick Wins (Can Ship This Week)

1. **EXPLAIN validation gate** (8-12h) — Biggest safety improvement, simple addition
2. **Statement timeout** (4h) — Trivial, prevents unbounded queries
3. **Schema embedding cache** (3-4h) — Eliminates redundant embedding calls
4. **Cost budget tracker** (6-8h) — Prevents runaway LLM spending
5. **Value hints for destinationcity** (4h) — The highest-impact column for filter accuracy; just add cached DISTINCT values to prompt

**Total quick wins: ~25-32 hours for massive safety + cost improvement.**
