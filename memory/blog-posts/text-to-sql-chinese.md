# 从 68% 到接近 100%：我们如何打造一个越用越准的 Text-to-SQL 系统

## 引言

去年我们接到一个需求：让业务人员用自然语言查询一张超大领域表。数亿行数据，200 多个列，强制日期范围过滤，查询涉及复杂的领域特定逻辑。

第一版上线后，准确率 68%。三分之一的查询返回错误结果或直接报错。用户抱怨不断，信任度跌到谷底。

我们调研了业界现状。BIRD 基准测试上，最好的系统也就 72-75%。学术论文里的数字看起来漂亮，但那些是在干净的小 Schema 上跑出来的——换到我们 200+ 列、充满领域术语、枚举值大小写混乱的真实表上，所有方法都会打折。

六个月后，我们的系统精度逼近 100%，并且每天都在变好。不是因为我们找到了什么银弹，而是因为我们构建了一套**会学习的 Pipeline**。

本文完整讲解我们的技术方案：8 个核心组件、每个组件的可量化精度提升、飞轮效应的设计，以及我们踩过的所有坑。

---

## 一、为什么 LLM + Prompt 会遇到天花板

上线第一版时，我们的方案很直接：把完整 Schema 塞进 prompt，附上几个通用示例，让大语言模型生成 SQL。听起来合理，实际上有三个致命问题。

### 1. 列幻觉

200+ 列的 Schema 塞进 context，模型经常选错列。更糟的是，它会「发明」不存在的列名——把两个真实列名的片段拼在一起，生成一个看起来合理但根本不存在的列。我们统计过，早期 ~15% 的错误是列幻觉导致的。

### 2. 过滤值错误

这是最隐蔽的问题。用户问「轿车的销量」，模型在 WHERE 子句里写 `type = '轿车'`，但数据库里存的是 `'Sedan'`、`'sedan'` 甚至 `'SEDAN'`。SQL 能跑，零行返回，用户以为没数据。实际上是过滤值不匹配。

低基数枚举列（几十个可选值）是重灾区。模型不知道数据库里到底存了什么值，只能猜。猜错率惊人。

### 3. 结构正确 ≠ 语义正确

这才是最难的。SQL 语法正确，能执行，返回了数据——但数据是错的。比如用户问「上个月新增」，模型用了创建日期而不是生效日期；用户问「活跃用户」，模型没加状态过滤条件。这类错误无法通过语法检查发现。

### 天花板在哪里？

我们分析了为什么精度停在 ~68%：

- **Context 稀释**：200+ 列的描述占满了 context window，真正有用的信息被海量无关列淹没。模型的注意力被分散了。
- **泛化 few-shot 无效**：我们放了 5-10 个通用示例在 prompt 里，但领域查询千差万别，通用示例对「按季度对比去年同期增长率」这类领域问题毫无帮助。
- **没有执行前验证**：模型生成 SQL 后直接执行。没有人检查，没有二次确认。模型对自己生成的错误 SQL 充满信心。

这三个问题不是调 prompt 能解决的。我们需要系统性的工程方案。

---

## 二、8 个组件，每个都有可量化的精度提升

以下是我们逐步叠加的 8 个组件。每个组件独立可测，精度提升可量化。

### 1. 语义 Schema 链接器（+~10%）

**问题**：200+ 列全部塞进 prompt，模型被无关列干扰，列幻觉频发。

**方案**：对所有列名和列描述预先做 embedding 向量化。用户提问时，计算问题与所有列的余弦相似度，只选出最相关的 20-30 列注入 prompt。

```typescript
interface SchemaLinker {
  // 预计算：所有列的 embedding
  buildIndex(columns: ColumnMeta[]): VectorIndex;
  
  // 运行时：根据用户问题筛选相关列
  linkColumns(
    question: string, 
    index: VectorIndex, 
    topK?: number       // 默认 25
  ): ColumnMeta[];
}

// 核心逻辑
async function linkSchema(question: string): Promise<ColumnMeta[]> {
  const questionEmbedding = await embed(question);
  const scored = columns.map(col => ({
    column: col,
    score: cosineSimilarity(questionEmbedding, col.embedding)
  }));
  
  // 取 top-K，但始终保留强制列（如日期过滤列）
  const relevant = scored
    .sort((a, b) => b.score - a.score)
    .slice(0, TOP_K);
  
  const mandatory = columns.filter(c => c.isMandatory);
  return deduplicate([...relevant.map(r => r.column), ...mandatory]);
}
```

**效果**：+~10%。列幻觉从 ~15% 降到不到 1%。这是 ROI 最高的单个组件。

关键细节：强制列（如日期过滤列）无论相似度如何都必须保留。我们早期漏掉这一点，导致生成的 SQL 缺少必要的日期范围条件，查询扫全表，既慢又不符合业务规则。

### 2. 问题掩码 + 语义 Few-Shot 检索（+~6%）

**问题**：通用 few-shot 示例对领域查询几乎没帮助。「查询 2019 年各区域销量」和「查询 2023 年各区域销量」的 SQL 结构完全一样，但如果只用原始问题做检索，它们的相似度会被年份差异拉低。

**方案**：先对问题做掩码处理——把数值、日期、专有名词替换为占位符——然后用掩码后的问题从 pgvector 检索语义相似的已验证 question→SQL 对。

```typescript
function maskQuestion(question: string): string {
  return question
    .replace(/\d{4}[-/年]\d{1,2}[-/月]?(\d{1,2}[日号]?)?/g, '<DATE>')
    .replace(/\d+(\.\d+)?%?/g, '<NUM>')
    .replace(/「[^」]+」|"[^"]+"/g, '<ENTITY>');
}

// "2023年第三季度销量超过5000的区域" 
// → "<DATE><ENTITY>销量超过<NUM>的区域"

async function retrieveFewShot(
  question: string, 
  k: number = 5
): Promise<FewShotPair[]> {
  const masked = maskQuestion(question);
  const embedding = await embed(masked);
  
  // pgvector 近似最近邻检索
  const pairs = await db.query(`
    SELECT question, sql, verified_at 
    FROM few_shot_cache 
    WHERE rule_version = $1
    ORDER BY embedding <=> $2 
    LIMIT $3
  `, [currentRuleVersion, embedding, k]);
  
  return pairs;
}
```

**效果**：+~6%。领域特定查询的准确率大幅提升，因为模型现在能看到结构相似的真实 SQL 范例。

### 3. 执行前 LLM 自审（+~5%）

**问题**：模型生成的 SQL 经常有细微错误——漏了一个过滤条件、JOIN 方向搞反、聚合粒度不对。

**方案**：生成 SQL 后，发送给第二个 LLM 实例做审查。审查者检查 SQL 是否正确回答了原始问题。如果发现问题，重新生成。最多循环 3 轮（我们称之为 RRIL —— Review-Regenerate-Iterate Loop）。

```typescript
async function generateWithReview(
  question: string, 
  schema: ColumnMeta[], 
  fewShot: FewShotPair[]
): Promise<{ sql: string; confidence: number }> {
  
  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    const { sql, confidence } = await generateSQL(question, schema, fewShot);
    
    // 高置信度 且 非首次 → 跳过审查
    if (confidence >= 0.90 && attempt > 0) {
      return { sql, confidence };
    }
    
    const review = await reviewSQL({ question, sql, schema });
    
    if (review.approved) {
      return { sql, confidence: Math.max(confidence, review.confidence) };
    }
    
    // 审查不通过 → 带上审查意见重新生成
    fewShot = [...fewShot, { 
      question, 
      sql, 
      note: `REJECTED: ${review.reason}` 
    }];
  }
  
  // 3 轮都没通过 → 标记为低置信度，走人工审核
  return { sql: lastAttempt.sql, confidence: 0.3 };
}
```

**效果**：+~5%，对复杂多条件查询尤其有效。自审不仅提升了精度，还提供了置信度分数，为后续的飞轮机制提供了信号。

触发条件很重要：我们不是每条 SQL 都走审查。只有置信度 < 0.70 或首次生成时才触发，避免不必要的 token 消耗。

### 4. 列值采样（+~3-4%）

**问题**：低基数枚举列的值，模型只能猜。猜错就是零行返回。

**方案**：预先对所有低基数列（唯一值 < 500 个）采样 20-50 个真实值，注入 prompt 中对应列的描述里。

```typescript
async function sampleColumnValues(
  column: ColumnMeta,
  sampleSize: number = 30
): Promise<string[]> {
  const values = await db.query(`
    SELECT DISTINCT "${column.name}" 
    FROM domain_table 
    WHERE "${column.name}" IS NOT NULL 
    LIMIT $1
  `, [sampleSize]);
  
  return values.map(v => v[column.name]);
}

// 注入 prompt 时的格式：
// 列名: category_type
// 描述: 类别类型
// 示例值: ["Sedan", "SUV", "Truck", "Coupe", "Hatchback", ...]
```

**效果**：+~3-4%。枚举值匹配错误从 ~12% 降到接近 0。这是投入最小、见效最快的组件——两天就能上线。

### 5. 查询复杂度路由（降本 + 提质）

不是所有查询都需要最强的模型。我们对查询做复杂度分类，路由到不同模型：

| 复杂度 | 特征 | 模型选择 | 占比 |
|--------|------|---------|------|
| 简单 | 单表聚合，无子查询 | Haiku（快、便宜） | ~60% |
| 中等 | 含 JOIN、领域过滤 | Sonnet（均衡） | ~30% |
| 复杂 | YoY 对比、多维分析、窗口函数 | Opus（最高质量） | ~10% |

```typescript
function classifyComplexity(question: string): 'simple' | 'medium' | 'complex' {
  const markers = {
    complex: [/同比|环比|yoy|对比.*去年/, /趋势|变化率/, /排名.*前\d+/],
    medium: [/分[组别]|按.*维度/, /筛选|过滤.*且/, /关联|join/i],
  };
  
  if (markers.complex.some(r => r.test(question))) return 'complex';
  if (markers.medium.some(r => r.test(question))) return 'medium';
  return 'simple';
}
```

**效果**：总成本降低 ~70%，精度不降反升（复杂查询用了更强的模型）。

### 6. 规则版本化 Embedding 缓存（一致性保障）

业务规则会变。强制过滤器会增删，列会废弃。如果缓存的 SQL 对基于旧规则生成，直接复用会出问题。

我们的方案：每个缓存的 question→SQL 对都存储生成时的规则版本哈希。规则变更时，批量重新计算所有缓存对的合规分数，自动标记不合规的对。

```typescript
interface CachedPair {
  question: string;
  maskedQuestion: string;
  sql: string;
  embedding: number[];
  ruleVersionHash: string;    // 生成时的规则版本
  complianceScore: number;    // 0-1，当前规则下的合规分数
  verifiedAt: Date;
  verifiedBy: 'auto' | 'human';
}

async function onRuleChange(newRules: BusinessRules): Promise<void> {
  const newHash = hash(newRules);
  const allPairs = await db.query('SELECT * FROM few_shot_cache');
  
  for (const pair of allPairs) {
    const score = evaluateCompliance(pair.sql, newRules);
    await db.query(
      'UPDATE few_shot_cache SET compliance_score = $1, rule_version_hash = $2 WHERE id = $3',
      [score, newHash, pair.id]
    );
  }
  
  // 合规分数低于阈值的自动停用
  await db.query(
    'UPDATE few_shot_cache SET active = false WHERE compliance_score < $1',
    [COMPLIANCE_THRESHOLD]
  );
}
```

### 7. Pipeline 全链路追踪（可观测性）

每次查询，我们记录完整的 Pipeline 执行链路：

```typescript
interface QueryTrace {
  traceId: string;
  question: string;
  // Schema 链接
  linkedColumns: string[];
  columnScores: Record<string, number>;
  // Few-shot 检索
  retrievedPairs: { question: string; similarity: number }[];
  // 生成
  generatedSQL: string;
  confidence: number;
  modelUsed: string;
  // 自审
  reviewResult?: { approved: boolean; reason?: string; attempt: number };
  // 执行
  executionTimeMs: number;
  rowCount: number;
  // 成本
  tokensUsed: { input: number; output: number };
  cachedTokens: number;
  // 反馈
  userFeedback?: 'correct' | 'incorrect' | null;
}
```

全部存为 JSONB，扩展现有的查询日志表。零新依赖。这不是可选项——没有追踪，每次调试都是在黑箱里猜。有了追踪，我们能精确定位「Schema 链接选错了列」还是「few-shot 检索返回了不相关的示例」还是「模型推理本身出了问题」。

### 8. Prompt 前缀缓存（延迟 + 成本）

Schema 描述、业务规则、通用指令——这些在数千次查询中是不变的。我们利用 API 的 prompt 缓存能力，把这些不变的部分作为前缀缓存。每次查询只需发送变化的部分（用户问题 + 动态选中的列 + 检索到的 few-shot 示例）。

**效果**：Token 消耗降低 ~40%，首 token 延迟降低 ~30%。

---

## 三、飞轮效应 —— 为什么这比任何静态基准都强

以上 8 个组件叠加后，系统精度从 68% 提升到 ~89%。但真正让我们逼近 100% 的，是飞轮。

```
用户提问
   ↓
Pipeline 生成 SQL + 置信度分数
   ↓
├─ 高置信度（≥ 0.90）→ 自动审批 → 推送到 Embedding 缓存
└─ 低置信度（< 0.90）→ 人工审核 → 审核通过后推送到缓存
   ↓
下次相似问题 → 缓存命中 → 直接返回（跳过 LLM 调用）
   ↓
用户反馈纠错 → 直接更新缓存中的 SQL
   ↓
缓存持续增长 → 命中率持续提升 → 精度趋近 100%
```

飞轮的核心逻辑：**每一次正确的查询都让系统更聪明，每一次纠错都消灭一类错误。**

我们观察到的数据趋势：

| 时间节点 | 精度 | 缓存命中率 | LLM 调用比例 |
|----------|------|-----------|-------------|
| 第 1 天 | ~89% | 0% | 100% |
| 第 4 周 | ~94% | ~40% | ~60% |
| 第 6 个月 | ~97% | ~70% | ~30% |
| 稳态 | ~99%+ | ~80-90% | ~10-20% |

**这意味着什么？**

精度和成本同时优化。缓存命中率越高，LLM 调用越少，成本越低。同时，因为缓存的 SQL 都是经过验证的，命中缓存的查询精度接近 100%。

**关键洞见**：BIRD 基准测试测的是冻结系统——给定一个固定的 Schema 和问题集，模型跑一次，出分。我们的系统不是冻结的，它每天都在学习。每个用户的每次查询都在训练这个系统。

这不是传统意义上的「模型训练」，不需要 GPU、不需要微调。它是工程层面的增强学习——用缓存和人工反馈构建一个不断膨胀的「正确答案库」。

静态基准测的是地板。飞轮决定天花板。

---

## 四、剩下的 1-3%

即便飞轮转起来了，仍有 1-3% 的查询是系统搞不定的。这些是真正困难的部分：

- **全新查询模式**：系统从未见过的查询结构。缓存里没有相似的对，few-shot 检索返回的示例帮助有限。这类查询只能靠 LLM 硬推理。
- **模糊自然语言**：用户问「最近的数据」——上周？上月？上季度？没有上下文无法判断。系统需要歧义检测能力，在无法确定时主动追问而不是猜。
- **数据漂移**：新增的枚举值还没被采样。新的业务类型上线了，但列值采样还是上一轮的快照。

我们的应对：

1. 定期刷新列值采样（每周自动执行）
2. 对歧义词（「最近」「大量」「主要」）做检测，低置信度时返回澄清问题
3. 缓存未命中 + 低置信度的查询自动进入人工审核队列

剩下的 1-3% 永远不会归零。但飞轮保证这个数字只会缩小，不会扩大。

---

## 五、经验总结

回头看这半年的迭代，如果让我重新开始，优先级会是这样：

**第一步：列值采样。** 两天的工作量，立竿见影。枚举值错误是最容易消灭的一类错误——你甚至不需要改模型或改 prompt，只需要把真实值告诉它。

**第二步：全链路追踪。** 在没有追踪的时候，每次调试我们都在猜——是 Schema 链接的问题还是 few-shot 检索的问题还是模型推理的问题？有了追踪后，调试效率提升了 10 倍。先建追踪，再做优化。

**第三步：Schema 链接器。** 这是杠杆最高的单个组件。+10% 的精度提升，同时大幅减少了 context window 的浪费。如果你的表有超过 50 列，这个组件是必须的。

**第四步：人工反馈飞轮。** 不要把人工审核当作系统不够好的妥协。它是架构决策——它是逼近 100% 的核心机制。没有人工反馈，你的系统永远停在某个固定精度上。

---

## 结语

Text-to-SQL 不是一个「选对模型就能解决」的问题。它是一个系统工程问题。

检索增强（Schema 链接 + 语义 few-shot）消灭了信息不足的错误。执行前自审消灭了推理层面的错误。列值采样消灭了数据层面的错误。飞轮把每一次成功和每一次纠错都转化为系统的永久知识。

静态基准测的是地板。飞轮决定天花板。

---

## 核心要点

1. **列值采样是性价比最高的优化** —— 投入两天，消灭一整类错误。如果你只做一件事，做这个。
2. **Schema 链接器是杠杆最大的组件** —— 200+ 列的表必须做列筛选，否则 context 稀释会严重拖累精度。
3. **先建追踪，再做优化** —— 没有全链路追踪的 Text-to-SQL 系统就是黑箱。你无法优化你看不到的东西。
4. **人工反馈不是妥协，是架构** —— 飞轮的核心燃料是人工验证和纠错。它是系统逼近 100% 的唯一路径。
5. **飞轮效应让精度和成本同时优化** —— 缓存命中率越高，LLM 调用越少，成本越低，精度越高。这是正循环，不是权衡。
