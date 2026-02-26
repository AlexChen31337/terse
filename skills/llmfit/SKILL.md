# llmfit Skill

Hardware-aware LLM model fitness scoring integrated with the intelligent-router.

## What it does

1. **Install** llmfit CLI (Rust binary via install script)
2. **Scan** hardware on local machine and GPU server (peter@10.0.0.44)
3. **Cache** results as JSON in `skills/llmfit/data/`
4. **Integrate** with intelligent-router — spawn_helper uses hardware fit scores to filter/rerank model selection

## Commands

```bash
# Run a scan and cache results
uv run python skills/llmfit/scripts/scan.py [--host local|gpu-server|all]

# Query cached fit scores
uv run python skills/llmfit/scripts/query.py --model "llama-3.3-70b" [--host gpu-server]

# Refresh cache (re-scan all hosts)
uv run python skills/llmfit/scripts/scan.py --refresh
```

## Integration with intelligent-router

`spawn_helper.py` checks `skills/llmfit/data/hardware_fits.json` before recommending a model.
If a model has a "marginal" or "no-fit" score on available hardware, it gets deprioritized in the fallback chain.

## Data Format

`data/hardware_fits.json`:
```json
{
  "scanned_at": "2026-02-26T17:00:00+11:00",
  "hosts": {
    "local": {
      "system": { "cpu": "...", "ram_gb": 32, "gpus": [] },
      "models": [
        { "name": "Llama-3.3-70B", "provider": "ollama", "score": 0.85, "fit": "good", "quant": "Q4_K_M", "mem_pct": 72, "tok_s": 12.5 }
      ]
    },
    "gpu-server": {
      "system": { "cpu": "...", "ram_gb": 16, "swap_gb": 256, "gpus": ["RTX 3090 24GB", "RTX 3080 10GB", "RTX 2070S 8GB"] },
      "models": [...]
    }
  }
}
```

## Files

- `scripts/scan.py` — Run llmfit on hosts, parse JSON output, cache
- `scripts/query.py` — Query cached scores for a specific model
- `scripts/integrate.py` — Patch intelligent-router to use hardware fits
- `data/hardware_fits.json` — Cached scan results
