#!/usr/bin/env python3
"""
llmfit integrate — patches intelligent-router to use hardware fitness data.

What it does:
1. Reads skills/llmfit/data/hardware_fits.json
2. For each model in intelligent-router/config.json, finds the best hardware fitness
   match across all scanned hosts and adds a `hardware_fit` field.
3. Patches intelligent-router/scripts/spawn_helper.py to deprioritize models with
   fit="marginal" or fit="none" in fallback chains.
   (Does NOT touch router.py scoring logic.)

Usage:
    uv run python skills/llmfit/scripts/integrate.py [--dry-run] [--verbose]
"""

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORKSPACE = Path(__file__).parent.parent.parent.parent
SKILL_DIR = Path(__file__).parent.parent
HARDWARE_FITS_FILE = SKILL_DIR / "data" / "hardware_fits.json"
ROUTER_DIR = WORKSPACE / "skills" / "intelligent-router"
CONFIG_FILE = ROUTER_DIR / "config.json"
SPAWN_HELPER_FILE = ROUTER_DIR / "scripts" / "spawn_helper.py"

# Marker tokens injected into spawn_helper.py — used to detect existing patches
PATCH_MARKER_START = "# [llmfit-integration-start]"
PATCH_MARKER_END = "# [llmfit-integration-end]"


# ---------------------------------------------------------------------------
# Name normalisation for fuzzy matching
# ---------------------------------------------------------------------------

def _normalise(name: str) -> str:
    """Lowercase, strip punctuation and common vendor prefixes for matching."""
    name = name.lower()
    # Strip HuggingFace org prefixes like "meta-llama/", "deepseek-ai/", "qwen/"
    if "/" in name:
        name = name.split("/")[-1]
    name = re.sub(r"[^a-z0-9]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _tokens(name: str) -> set[str]:
    return set(_normalise(name).split())


def _match_score(router_id: str, alias: str, llmfit_name: str) -> float:
    """
    Return a similarity score [0, 1] between a router model id/alias and a
    llmfit model name. Higher is better; 0 means no meaningful overlap.
    """
    llm_toks = _tokens(llmfit_name)
    # Try both the bare id and the alias
    cand_toks = _tokens(router_id) | _tokens(alias)

    if not llm_toks or not cand_toks:
        return 0.0

    overlap = llm_toks & cand_toks
    if not overlap:
        return 0.0

    # Jaccard-like, but weighted by token importance (param-count tokens matter more)
    # Param-count tokens: "7b", "70b", "32b", "14b", "72b", "8b", etc.
    param_pattern = re.compile(r"^\d+\.?\d*b$")
    param_weight = 3.0
    overlap_score = sum(param_weight if param_pattern.match(t) else 1.0 for t in overlap)
    union = llm_toks | cand_toks
    union_score = sum(param_weight if param_pattern.match(t) else 1.0 for t in union)

    return overlap_score / union_score


def find_best_fit(router_id: str, alias: str, hardware_fits: dict) -> Optional[dict]:
    """
    Find the best-matching llmfit entry for a router model across all hosts.
    Returns the entry with the highest score (taking best fit across hosts), or None.
    """
    best_entry: Optional[dict] = None
    best_similarity = 0.0

    for host, host_data in hardware_fits.get("hosts", {}).items():
        for model in host_data.get("models", []):
            sim = _match_score(router_id, alias, model.get("name", ""))
            if sim > best_similarity and sim >= 0.3:  # min threshold
                best_similarity = sim
                best_entry = {**model, "host": host, "match_score": round(sim, 3)}

    return best_entry


# ---------------------------------------------------------------------------
# Config patching
# ---------------------------------------------------------------------------

def patch_config(hardware_fits: dict, dry_run: bool, verbose: bool) -> int:
    """
    Add `hardware_fit` field to each model entry in config.json.
    Returns number of models patched.
    """
    with open(CONFIG_FILE) as f:
        config = json.load(f)

    patched = 0
    for model in config.get("models", []):
        model_id = model.get("id", "")
        alias = model.get("alias", "")
        match = find_best_fit(model_id, alias, hardware_fits)

        if match:
            hw_fit = {
                "fit": match.get("fit", "unknown"),
                "fit_level": match.get("fit_level", ""),
                "score": match.get("score"),
                "tok_s": match.get("tok_s"),
                "quant": match.get("quant", ""),
                "run_mode": match.get("run_mode", ""),
                "host": match.get("host", ""),
                "llmfit_name": match.get("name", ""),
                "match_confidence": match.get("match_score", 0),
                "updated_at": datetime.now(timezone.utc).astimezone().isoformat(),
            }
            model["hardware_fit"] = hw_fit
            patched += 1
            if verbose:
                print(
                    f"   ✅ {model_id!r} → fit={hw_fit['fit']!r} "
                    f"(matched {hw_fit['llmfit_name']!r} @ {hw_fit['match_confidence']:.2f})"
                )
        else:
            # No hardware data → mark as unknown so spawn_helper knows
            model["hardware_fit"] = {
                "fit": "unknown",
                "updated_at": datetime.now(timezone.utc).astimezone().isoformat(),
            }
            if verbose:
                print(f"   ❓ {model_id!r} — no llmfit match found")

    if dry_run:
        print(f"\n[dry-run] Would patch {patched} models in {CONFIG_FILE}")
        return patched

    backup = CONFIG_FILE.with_suffix(".json.bak")
    shutil.copy2(CONFIG_FILE, backup)

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print(f"✅ Patched {patched} models in {CONFIG_FILE}  (backup: {backup.name})")
    return patched


# ---------------------------------------------------------------------------
# spawn_helper.py patching
# ---------------------------------------------------------------------------

SPAWN_HELPER_PATCH = '''\
# [llmfit-integration-start]
# Hardware fitness filtering for fallback chains.
# Added by: uv run python skills/llmfit/scripts/integrate.py
# Do NOT remove the marker comments — they allow re-patching to be idempotent.
import functools as _functools

_HARDWARE_FITS_FILE = Path(__file__).parent.parent.parent / "llmfit" / "data" / "hardware_fits.json"
_DEPRIORITIZE_FITS = {"marginal", "none"}  # fits to push to end of fallback chain


@_functools.lru_cache(maxsize=1)
def _load_hardware_fits() -> dict:
    """Load llmfit hardware fitness cache (cached for process lifetime)."""
    if not _HARDWARE_FITS_FILE.exists():
        return {}
    try:
        with open(_HARDWARE_FITS_FILE) as _f:
            return json.load(_f)
    except Exception:
        return {}


def get_hardware_fit(model_id: str) -> str:
    """
    Return the canonical fit string for a model_id (e.g. "good", "marginal", "none").
    Looks up the hardware_fit field added by integrate.py in config.json.
    Falls back to "unknown" if not found.
    """
    try:
        cfg = load_config()
        for entry in cfg.get("models", []):
            eid = entry.get("id", "")
            provider = entry.get("provider", "")
            # Match by full "provider/id" or bare "id"
            full_id = f"{provider}/{eid}" if provider else eid
            if model_id in (eid, full_id) or full_id.endswith(model_id):
                hw = entry.get("hardware_fit", {})
                return hw.get("fit", "unknown")
    except Exception:
        pass
    return "unknown"


def rerank_fallback_chain(chain: list) -> list:
    """
    Move models with fit="marginal" or fit="none" to the end of the fallback chain.
    Models with unknown/good/perfect fit keep their original order.
    This does NOT remove any models — just reranks for hardware awareness.
    """
    fits = [(model_id, get_hardware_fit(model_id)) for model_id in chain]
    preferred = [mid for mid, fit in fits if fit not in _DEPRIORITIZE_FITS]
    deprioritized = [mid for mid, fit in fits if fit in _DEPRIORITIZE_FITS]
    return preferred + deprioritized
# [llmfit-integration-end]
'''


def _strip_existing_patch(source: str) -> str:
    """Remove any previously injected llmfit patch block from spawn_helper.py."""
    pattern = re.compile(
        rf"{re.escape(PATCH_MARKER_START)}.*?{re.escape(PATCH_MARKER_END)}\n?",
        re.DOTALL,
    )
    return pattern.sub("", source)


def _inject_patch_after_imports(source: str, patch: str) -> str:
    """Inject the patch block after the last top-level import statement."""
    lines = source.splitlines(keepends=True)
    last_import_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            last_import_idx = i

    insert_at = last_import_idx + 1 if last_import_idx >= 0 else 0
    lines.insert(insert_at, "\n" + patch + "\n")
    return "".join(lines)


def _patch_classify_task(source: str) -> str:
    """
    Inject rerank_fallback_chain call into the main() display of fallback_chain.
    Idempotent: only patches if not already patched.

    Target line (from spawn_helper.py main()):
        fallback_chain = config.get("routing_rules", {}).get(tier, {}).get("fallback_chain", [])

    We add reranking directly after that assignment.
    """
    marker = "# [llmfit-rerank-applied]"
    if marker in source:
        return source  # already patched

    target = '    fallback_chain = config.get("routing_rules", {}).get(tier, {}).get("fallback_chain", [])'
    replacement = (
        target
        + "\n"
        + f"    fallback_chain = rerank_fallback_chain(fallback_chain)  {marker}"
    )
    return source.replace(target, replacement, 1)  # only replace first occurrence


def patch_spawn_helper(dry_run: bool, verbose: bool) -> None:
    """Inject hardware fitness reranking into spawn_helper.py."""
    with open(SPAWN_HELPER_FILE) as f:
        original = f.read()

    # Remove any previous patch (idempotent)
    cleaned = _strip_existing_patch(original)
    # Inject the helper functions after imports
    patched = _inject_patch_after_imports(cleaned, SPAWN_HELPER_PATCH)
    # Inject the rerank call in main()
    patched = _patch_classify_task(patched)

    if patched == original:
        print("ℹ️  spawn_helper.py already up to date.")
        return

    if dry_run:
        print(f"[dry-run] Would patch {SPAWN_HELPER_FILE}")
        if verbose:
            # Show diff summary
            orig_lines = original.splitlines()
            new_lines = patched.splitlines()
            added = len(new_lines) - len(orig_lines)
            print(f"   +{added} lines")
        return

    backup = SPAWN_HELPER_FILE.with_suffix(".py.bak")
    shutil.copy2(SPAWN_HELPER_FILE, backup)
    with open(SPAWN_HELPER_FILE, "w") as f:
        f.write(patched)
    print(f"✅ Patched {SPAWN_HELPER_FILE}  (backup: {backup.name})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Integrate llmfit hardware fitness data into intelligent-router."
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-model match details")
    args = parser.parse_args()

    if not HARDWARE_FITS_FILE.exists():
        print(
            f"❌ No hardware fits cache found at {HARDWARE_FITS_FILE}.\n"
            "   Run first: uv run python skills/llmfit/scripts/scan.py --host all"
        )
        raise SystemExit(1)

    print(f"📂 Loading hardware fits from {HARDWARE_FITS_FILE}")
    with open(HARDWARE_FITS_FILE) as f:
        hardware_fits = json.load(f)

    scanned_at = hardware_fits.get("scanned_at", "unknown")
    print(f"   Cache timestamp: {scanned_at}")

    host_summaries = []
    for host, data in hardware_fits.get("hosts", {}).items():
        n = len(data.get("models", []))
        host_summaries.append(f"{host}={n}")
    print(f"   Hosts: {', '.join(host_summaries)}")

    print(f"\n🔧 Patching {CONFIG_FILE.name} (adding hardware_fit fields)...")
    n_patched = patch_config(hardware_fits, args.dry_run, args.verbose)

    print(f"\n🔧 Patching {SPAWN_HELPER_FILE.name} (adding rerank_fallback_chain)...")
    patch_spawn_helper(args.dry_run, args.verbose)

    print(f"\n✅ Integration complete — {n_patched} models tagged with hardware fitness.")
    if args.dry_run:
        print("   (dry-run: no files were modified)")


if __name__ == "__main__":
    main()
