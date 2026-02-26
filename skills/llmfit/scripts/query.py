#!/usr/bin/env python3
"""
llmfit query — look up cached hardware-fitness scores by model name.

Usage:
    uv run python skills/llmfit/scripts/query.py --model "llama-3.3-70b"
    uv run python skills/llmfit/scripts/query.py --model "deepseek" --host gpu-server
    uv run python skills/llmfit/scripts/query.py --model "qwen" --json
    uv run python skills/llmfit/scripts/query.py --list-all [--host local]

The match is case-insensitive substring match against the model `name` field.
"""

import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
HARDWARE_FITS_FILE = SKILL_DIR / "data" / "hardware_fits.json"


def load_cache() -> dict:
    if not HARDWARE_FITS_FILE.exists():
        print(
            f"❌ No cache found at {HARDWARE_FITS_FILE}.\n"
            "   Run: uv run python skills/llmfit/scripts/scan.py --host all",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(HARDWARE_FITS_FILE) as f:
        return json.load(f)


def search_models(cache: dict, query: str, host: str | None = None) -> list[dict]:
    """Return all models whose name contains `query` (case-insensitive)."""
    q = query.lower()
    results: list[dict] = []
    hosts_data = cache.get("hosts", {})

    for h, data in hosts_data.items():
        if host and h != host:
            continue
        for model in data.get("models", []):
            name = model.get("name", "")
            if q in name.lower():
                results.append({"host": h, **model})

    return results


def list_all_models(cache: dict, host: str | None = None) -> list[dict]:
    """Return all models from all hosts (or a specific host)."""
    results: list[dict] = []
    for h, data in cache.get("hosts", {}).items():
        if host and h != host:
            continue
        for model in data.get("models", []):
            results.append({"host": h, **model})
    return results


def format_result(result: dict) -> str:
    fit_emoji = {
        "perfect": "✅",
        "good": "🟢",
        "marginal": "⚠️ ",
        "none": "❌",
    }.get(result.get("fit", ""), "❓")

    lines = [
        f"  {fit_emoji} [{result['host']}] {result.get('name', '?')}",
        f"     Score:    {result.get('score', '?')}  |  Fit: {result.get('fit_level', result.get('fit', '?'))}",
        f"     Quant:    {result.get('quant', '?')}  |  Run mode: {result.get('run_mode', '?')}",
        f"     VRAM:     {result.get('mem_required_gb', '?')} GB req / {result.get('mem_available_gb', '?')} GB avail",
        f"     Speed:    {result.get('tok_s', '?')} tok/s  |  Util: {result.get('utilization_pct', '?')}%",
        f"     Params:   {result.get('parameter_count', '?')}  |  Category: {result.get('category', '?')}",
    ]
    if result.get("notes"):
        lines.append(f"     Notes:    {'; '.join(result['notes'])}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query cached llmfit hardware-fitness scores."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--model", "-m", help="Model name (substring, case-insensitive)")
    group.add_argument("--list-all", "-l", action="store_true", help="List all cached models")

    parser.add_argument(
        "--host",
        choices=["local", "gpu-server"],
        default=None,
        help="Filter by host (default: all hosts)",
    )
    parser.add_argument("--json", "-j", action="store_true", dest="json_out", help="Output as JSON")
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Only show models with score >= this value",
    )
    parser.add_argument(
        "--fit",
        choices=["perfect", "good", "marginal", "none"],
        default=None,
        help="Filter by fit level",
    )
    args = parser.parse_args()

    cache = load_cache()
    scanned_at = cache.get("scanned_at", "unknown")

    if args.list_all:
        results = list_all_models(cache, args.host)
    else:
        results = search_models(cache, args.model, args.host)

    # Apply optional filters
    if args.min_score is not None:
        results = [r for r in results if (r.get("score") or 0) >= args.min_score]
    if args.fit:
        results = [r for r in results if r.get("fit") == args.fit]

    if not results:
        label = f"'{args.model}'" if args.model else "any model"
        print(f"No results found for {label}" + (f" on {args.host}" if args.host else "") + ".")
        sys.exit(0)

    if args.json_out:
        print(json.dumps({"scanned_at": scanned_at, "results": results}, indent=2))
    else:
        host_label = f" on {args.host}" if args.host else ""
        label = f"'{args.model}'" if args.model else "all models"
        print(f"\n🔎 Hardware fitness for {label}{host_label}  (cache: {scanned_at})\n")
        for r in results:
            print(format_result(r))
            print()


if __name__ == "__main__":
    main()
