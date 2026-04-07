#!/usr/bin/env python3
"""
Write advice JSON from stdin (agent output) to the advice file.
Validates schema and clamps values to safety bounds before writing.

Usage: echo '{"export_threshold": 8.5, ...}' | uv run python scripts/write_advice.py
"""
import json
import sys
from datetime import datetime, timezone

ADVICE_FILE = "/ha-smartshift/.ai_advice.json"
BMS_FLOOR_FILE = "/ha-smartshift/.bms_floor.json"

# Safety bounds — deterministic script also enforces these
# discharge_floor lower bound is dynamically read from BMS detection

def get_bms_floor() -> float:
    """Read auto-detected BMS floor from inverter behavior cache."""
    try:
        with open(BMS_FLOOR_FILE) as f:
            data = json.load(f)
        if data.get("source") == "bms_detection" and data.get("soc_min"):
            return float(data["soc_min"])
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return 5.0  # fallback

BOUNDS = {
    "export_threshold": (3.0, 30.0),
    "discharge_floor": (get_bms_floor(), 60.0),
    "confidence": (0.0, 1.0),
}

REQUIRED_FIELDS = ["export_threshold", "discharge_floor", "strategy", "reasoning"]
VALID_STRATEGIES = [
    "aggressive_export", "moderate_export", "conservative_hold",
    "grid_charge", "emergency_hold",
]

def clamp(value, low, high):
    return max(low, min(high, value))

def main():
    try:
        raw = sys.stdin.read().strip()
        # Try to extract JSON from potential markdown code blocks
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        advice = json.loads(raw)
    except (json.JSONDecodeError, IndexError) as e:
        print(f"ERROR: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate required fields
    missing = [f for f in REQUIRED_FIELDS if f not in advice]
    if missing:
        print(f"ERROR: Missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)

    # Validate strategy
    if advice["strategy"] not in VALID_STRATEGIES:
        print(f"WARNING: Unknown strategy '{advice['strategy']}', proceeding anyway", file=sys.stderr)

    # Clamp to safety bounds
    for field, (low, high) in BOUNDS.items():
        if field in advice and isinstance(advice[field], (int, float)):
            original = advice[field]
            advice[field] = clamp(float(advice[field]), low, high)
            if advice[field] != original:
                print(f"CLAMPED: {field} {original} → {advice[field]} (bounds: {low}-{high})", file=sys.stderr)

    # Add metadata
    advice["written_at"] = datetime.now(timezone.utc).isoformat()
    advice.setdefault("confidence", 0.5)
    advice.setdefault("alerts", [])

    # Write
    with open(ADVICE_FILE, "w") as f:
        json.dump(advice, f, indent=2)

    print(f"Advice written to {ADVICE_FILE}")
    print(json.dumps(advice, indent=2))

if __name__ == "__main__":
    main()
