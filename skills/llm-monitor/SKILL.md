---
name: llm-monitor
description: Monitor frontier and open-source LLM developments via Twitter/X. Tracks major labs (OpenAI, Anthropic, DeepMind, Meta, Mistral, xAI) and key researchers (Karpathy, LeCun, etc.) for releases, benchmarks, and SOTA announcements.
---

# LLM Monitor

This skill allows agents to monitor the AI landscape for breaking news, model releases, and significant discussions.

## Usage

This skill provides a script `monitor.py` that uses the `bird` CLI (Twitter) to check for updates from a curated list of AI labs and researchers.

### Run a Monitoring Check

```bash
# Basic check (defaults to last 24h)
python3 skills/llm-monitor/monitor.py

# Check specific accounts or keywords
python3 skills/llm-monitor/monitor.py --focus "open source"
```

## Configuration

The monitor tracks two main groups:

### 1. Labs & Organizations
- OpenAI (@OpenAI)
- Anthropic (@AnthropicAI)
- Google DeepMind (@GoogleDeepMind)
- Meta AI (@MetaAI)
- Mistral AI (@MistralAI)
- xAI (@xai)
- Hugging Face (@huggingface)

### 2. Key Individuals
- Andrej Karpathy (@karpathy)
- Yann LeCun (@ylecun)
- Sam Altman (@sama)
- Demis Hassabis (@demishassabis)
- Greg Brockman (@gdb)
- Sawyer Hood (@sawyerhood) - for cursor/coding tools

## Dependencies

- `bird` CLI (must be authenticated)
- Python 3.x
