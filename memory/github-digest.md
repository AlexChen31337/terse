# GitHub Resources Digest
*Digested: 2026-03-02 | Alex Chen*

---

## 1. free-llm-api-resources — FREE API OPTIONS WE CAN USE TODAY

**Source:** https://github.com/cheahjs/free-llm-api-resources
**Digested from:** live README

### 🟢 Best Candidates for Alex's SIMPLE tier (replace NIM when it times out)

| Provider | Best Model | Daily Limit | Notes |
|----------|-----------|-------------|-------|
| **Groq** | Llama 3.3 70B | 1,000 req/day | 12k TPM. Fast inference. OpenAI-compatible API. **Best quality free option.** |
| **Groq** | Llama 3.1 8B | 14,400 req/day | 6k TPM. High volume, great for heartbeats/monitoring. |
| **Cerebras** | Llama 3.3 70B | 14,400 req/day | 1M tokens/day. Very generous. OpenAI-compatible. |
| **Cerebras** | Qwen 3 235B A22B | 14,400 req/day | 1M tokens/day — huge MoE model, FREE. |
| **OpenRouter** | Llama 3.3 70B :free | 50 req/day (1000 with $10 topup) | Convenient unified API. |
| **OpenRouter** | GLM-4.5 Air :free | 50/day | z-ai model, already know GLM quality |
| **GitHub Models** | DeepSeek-V3, GPT-4o, o3 | Copilot tier limits | OpenAI-compatible, already have GH account |
| **Google AI Studio** | Gemini 2.5 Flash | 20 req/day | 250k TPM. Good for complex single tasks. |
| **Mistral** | All models (free tier) | 500k TPM, 1B tokens/month | Requires phone verify + data opt-in. Huge allowance. |
| **Cloudflare Workers AI** | Llama 3.3 70B, Qwen 3 | 10k neurons/day | Ultra-low latency edge inference |

### 🔑 Action Items
1. **Sign up for Groq** (cloud.groq.com) — get API key, add to OpenClaw config as `groq/llama-3.3-70b`
2. **Sign up for Cerebras** (cloud.cerebras.ai) — 14,400 req/day Llama 70B FREE is the best deal here
3. **OpenRouter** already has GLM-4.5 Air free — if we topup $10, 1000 req/day unlocked
4. These can replace the NIM SIMPLE tier that's been timing out (8 consecutive failures logged)

### Routing suggestion
```
SIMPLE tasks → Groq Llama 3.1 8B (14,400/day, FREE)
MEDIUM tasks → Cerebras Llama 3.3 70B (14,400/day, FREE)  
COMPLEX → anthropic-proxy-1/claude-sonnet-4-6 (paid, as before)
```

---

## 2. MarkitDown (Microsoft) — INSTALLED ✅

**Source:** https://github.com/microsoft/markitdown
**Status:** Installed in workspace venv via `uv pip install markitdown`

### What it does
Converts: PDF, DOCX, PPTX, XLSX, HTML, Markdown, Images (with OCR), Audio (with transcription), ZIP archives → Clean Markdown

### Usage
```python
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("Bowen_Li_CV.docx")
print(result.text_content)
```

Or CLI:
```bash
uv run markitdown input.pdf > output.md
uv run markitdown input.docx > output.md
```

### Where we'll use it
- **MbD book pipeline**: Convert any uploaded DOCX/PDF drafts → Markdown for editing
- **CV updates**: Next time Bowen shares a new CV doc, convert instantly instead of parsing HTML
- **ClawChain docs**: Pull in PDF whitepapers, convert to Markdown for RAG/context
- **Email attachments**: When someone sends a PDF, convert before feeding to LLM

---

## 3. system-prompts-and-model-of-ai-tools — REPO STATUS

**Source:** https://github.com/x1xhol/system-prompts-and-model-of-ai-tools
**Status:** Repo appears to have been deleted or made private (404 on all endpoints)

### What we know it contained (from memory/references)
The repo was famous for collecting system prompts from:
- **Cursor** — how it defines its coding persona, tool usage rules, context window management
- **Devin** — the task decomposition and execution loop design
- **ChatGPT** — safety layers, capability declarations
- **Perplexity** — search integration and citation formatting rules
- **Claude** — self-referential system prompt structure

### Alternative sources
- **Cursor's CLAUDE.md approach**: Cursor ships a `.cursorrules` file in repos — we can read any public repo's `.cursorrules` to understand their agent config
- **Leaked Devin prompt** is archived at: https://gist.github.com (searchable)
- **OpenClaw's own prompt** is in our system prompt above — that's the real reference

### What we can learn from this pattern (even without the repo)
The key insight from top AI tools' system prompts:
1. **Role definition is crisp** — 1-2 sentences, not paragraphs
2. **Constraints are explicit** — what NOT to do is as important as what to do
3. **Tool instructions are contextual** — explain when to use each tool, not just what it does
4. **Fallback behaviour is specified** — what to do when uncertain
5. **Alex's SOUL.md + AGENTS.md** already follows this pattern better than most

---

## Summary: What We Actually Got

| Resource | Status | Immediate Value |
|----------|--------|-----------------|
| free-llm-api-resources | ✅ Fully digested | **Sign up for Groq + Cerebras → replace failing NIM SIMPLE tier** |
| MarkitDown | ✅ Installed & ready | Use for CV/doc/PDF processing from now on |
| system-prompts repo | ❌ 404 (deleted/private) | Patterns extracted from memory; check .cursorrules in public repos instead |

---

*Next action: Create Groq + Cerebras accounts and add to OpenClaw config*
