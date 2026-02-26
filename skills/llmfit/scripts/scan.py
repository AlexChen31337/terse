#!/usr/bin/env python3
"""
llmfit scan — runs `llmfit recommend --json --limit 50` locally and/or via SSH
on the GPU server, then merges results into data/hardware_fits.json.

Usage:
    uv run python skills/llmfit/scripts/scan.py [--host local|gpu-server|all] [--refresh]
    uv run python skills/llmfit/scripts/scan.py --host all --limit 50
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
HARDWARE_FITS_FILE = DATA_DIR / "hardware_fits.json"

GPU_SERVER_HOST = "peter@10.0.0.44"
GPU_SERVER_SSH_KEY = str(Path.home() / ".ssh" / "id_ed25519_alexchen")
LLMFIT_LOCAL = str(Path.home() / ".local" / "bin" / "llmfit")
LLMFIT_REMOTE = "~/.local/bin/llmfit"

# Map llmfit fit_level strings → canonical short strings used in hardware_fits.json
FIT_LEVEL_MAP = {
    "Perfect": "perfect",
    "Good": "good",
    "Marginal": "marginal",
    "No Fit": "none",
    "NoFit": "none",
    "None": "none",
}


def parse_system_info(system_text: str) -> dict:
    """Parse the plain-text output of `llmfit system` into a dict."""
    info: dict = {}
    gpus: list[str] = []
    for line in system_text.splitlines():
        line = line.strip()
        if line.startswith("CPU:"):
            info["cpu"] = line[4:].strip()
        elif line.startswith("Total RAM:"):
            val = line.split(":", 1)[1].strip()
            try:
                info["ram_gb"] = round(float(val.split()[0]), 1)
            except ValueError:
                info["ram_gb"] = val
        elif line.startswith("Available RAM:"):
            val = line.split(":", 1)[1].strip()
            try:
                info["ram_available_gb"] = round(float(val.split()[0]), 1)
            except ValueError:
                info["ram_available_gb"] = val
        elif line.startswith("GPU") and ":" in line and "VRAM" in line:
            # Handles both "GPU:" and "GPU 1:", "GPU 2:", etc.
            gpus.append(line.split(":", 1)[1].strip())
        elif line.startswith("Backend:"):
            info["backend"] = line.split(":", 1)[1].strip()
    info["gpus"] = gpus
    return info


def run_local_system_info() -> dict:
    """Get system info from the local machine."""
    result = subprocess.run(
        [LLMFIT_LOCAL, "system"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"llmfit system failed: {result.stderr}")
    return parse_system_info(result.stdout)


def run_local_scan(limit: int = 50) -> list[dict]:
    """Run llmfit recommend on local machine, return raw model list."""
    result = subprocess.run(
        [LLMFIT_LOCAL, "recommend", "--json", "--limit", str(limit)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"llmfit recommend failed locally: {result.stderr}")
    data = json.loads(result.stdout)
    return data.get("models", [])


def run_remote_system_info() -> dict:
    """Get system info from GPU server via SSH."""
    cmd = [
        "ssh",
        "-i", GPU_SERVER_SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=15",
        GPU_SERVER_HOST,
        f"{LLMFIT_REMOTE} system",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Remote llmfit system failed: {result.stderr}")
    return parse_system_info(result.stdout)


def run_remote_scan(limit: int = 50) -> list[dict]:
    """Run llmfit recommend on GPU server via SSH, return raw model list."""
    cmd = [
        "ssh",
        "-i", GPU_SERVER_SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=15",
        GPU_SERVER_HOST,
        f"{LLMFIT_REMOTE} recommend --json --limit {limit}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(f"Remote llmfit recommend failed: {result.stderr}")
    data = json.loads(result.stdout)
    return data.get("models", [])


def normalise_model(raw: dict) -> dict:
    """Normalise a raw llmfit model entry to our canonical schema."""
    fit_level_raw = raw.get("fit_level", "")
    fit = FIT_LEVEL_MAP.get(fit_level_raw, fit_level_raw.lower().replace(" ", "_") if fit_level_raw else "unknown")
    return {
        "name": raw.get("name", ""),
        "provider": raw.get("provider", ""),
        "score": raw.get("score"),
        "fit": fit,
        "fit_level": fit_level_raw,
        "quant": raw.get("best_quant", ""),
        "mem_required_gb": raw.get("memory_required_gb"),
        "mem_available_gb": raw.get("memory_available_gb"),
        "utilization_pct": raw.get("utilization_pct"),
        "tok_s": raw.get("estimated_tps"),
        "run_mode": raw.get("run_mode", ""),
        "params_b": raw.get("params_b"),
        "parameter_count": raw.get("parameter_count", ""),
        "category": raw.get("category", ""),
        "context_length": raw.get("context_length"),
        "runtime": raw.get("runtime", ""),
        "score_components": raw.get("score_components", {}),
        "notes": raw.get("notes", []),
    }


def load_existing() -> dict:
    """Load existing hardware_fits.json or return empty structure."""
    if HARDWARE_FITS_FILE.exists():
        with open(HARDWARE_FITS_FILE) as f:
            return json.load(f)
    return {"scanned_at": None, "hosts": {}}


def save(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(HARDWARE_FITS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved {HARDWARE_FITS_FILE}")


def scan_local(limit: int, verbose: bool = True) -> dict:
    if verbose:
        print("🔍 Scanning local machine...")
    system = run_local_system_info()
    models_raw = run_local_scan(limit)
    models = [normalise_model(m) for m in models_raw]
    if verbose:
        print(f"   local: {system.get('cpu','?')} | {system.get('gpus',[])} | {len(models)} models")
    return {"system": system, "models": models}


def scan_gpu_server(limit: int, verbose: bool = True) -> dict:
    if verbose:
        print("🔍 Scanning GPU server (peter@10.0.0.44)...")
    # GPU server has 3 GPUs; annotate known swap
    system = run_remote_system_info()
    system.setdefault("swap_gb", 256)  # known 256 GB swapfile on /data2
    models_raw = run_remote_scan(limit)
    models = [normalise_model(m) for m in models_raw]
    if verbose:
        print(f"   gpu-server: {system.get('cpu','?')} | {system.get('gpus',[])} | {len(models)} models")
    return {"system": system, "models": models}


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan hardware with llmfit and cache results.")
    parser.add_argument(
        "--host",
        choices=["local", "gpu-server", "all"],
        default="all",
        help="Which host(s) to scan (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max models to fetch per host (default: 50)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-scan (same as running with --host all)",
    )
    args = parser.parse_args()

    existing = load_existing()
    existing.setdefault("hosts", {})

    hosts_to_scan = (
        ["local", "gpu-server"]
        if args.host == "all" or args.refresh
        else [args.host]
    )

    errors: list[str] = []
    for host in hosts_to_scan:
        try:
            if host == "local":
                existing["hosts"]["local"] = scan_local(args.limit)
            elif host == "gpu-server":
                existing["hosts"]["gpu-server"] = scan_gpu_server(args.limit)
        except Exception as exc:
            msg = f"⚠️  {host}: {exc}"
            print(msg, file=sys.stderr)
            errors.append(msg)

    existing["scanned_at"] = datetime.now(timezone.utc).astimezone().isoformat()

    save(existing)

    if errors:
        print("\nCompleted with errors:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    # Summary
    for host, data in existing["hosts"].items():
        models = data.get("models", [])
        perfect = sum(1 for m in models if m.get("fit") == "perfect")
        good = sum(1 for m in models if m.get("fit") == "good")
        marginal = sum(1 for m in models if m.get("fit") == "marginal")
        none_ = sum(1 for m in models if m.get("fit") == "none")
        print(
            f"   {host}: {len(models)} models — "
            f"perfect={perfect} good={good} marginal={marginal} none={none_}"
        )


if __name__ == "__main__":
    main()
