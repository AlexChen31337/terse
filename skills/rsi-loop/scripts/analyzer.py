#!/usr/bin/env python3
"""
RSI Loop - Analyzer
Detects improvement patterns from logged outcomes.
Identifies the most impactful gaps for the synthesizer to address.
"""

import argparse
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
OUTCOMES_FILE = DATA_DIR / "outcomes.jsonl"
PATTERNS_FILE = DATA_DIR / "patterns.json"

def load_outcomes(days: int = 7):
    if not OUTCOMES_FILE.exists():
        return []
    cutoff = time.time() - (days * 86400)
    outcomes = []
    with open(OUTCOMES_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
                ts = datetime.fromisoformat(o["ts"]).timestamp()
                if ts >= cutoff:
                    outcomes.append(o)
            except Exception:
                pass
    return outcomes

def analyze(days: int = 7) -> dict:
    """
    Analyze outcomes and produce ranked improvement patterns.

    Pattern structure:
    {
      "id": "pattern-uuid",
      "category": "skill_gap|model_routing|context_loss|...",
      "task_type": "code_generation|...",
      "issue": "skill_gap",
      "frequency": 12,
      "impact_score": 0.85,   # frequency * avg_quality_delta
      "failure_rate": 0.60,
      "avg_quality": 2.1,
      "description": "Human-readable description",
      "sample_notes": ["...", "..."],
      "suggested_action": "Create skill|Update SOUL.md|Add cron|Fix routing",
    }
    """
    outcomes = load_outcomes(days)
    if not outcomes:
        return {"patterns": [], "meta": {"outcomes": 0, "days": days}}

    # ── Group by (task_type, issue) pairs ──────────────────────────────────────
    groups = defaultdict(list)
    for o in outcomes:
        task = o.get("task_type", "unknown")
        issues = o.get("issues", []) or ["none"]
        for issue in issues:
            groups[(task, issue)].append(o)

    # ── Score each group ───────────────────────────────────────────────────────
    patterns = []
    for (task, issue), group_outcomes in groups.items():
        n = len(group_outcomes)
        if n < 2:  # ignore one-offs
            continue

        failures = [o for o in group_outcomes if not o.get("success")]
        failure_rate = len(failures) / n
        avg_quality = sum(o.get("quality", 3) for o in group_outcomes) / n

        # quality deficit from ideal (5.0)
        quality_deficit = 5.0 - avg_quality

        # impact = frequency * quality deficit (normalized)
        impact = (n / len(outcomes)) * quality_deficit

        # Categorize
        if issue in ("skill_gap", "missing_tool", "wrong_output"):
            category = "skill_gap"
        elif issue in ("rate_limit", "model_fallback", "wrong_model_tier", "slow_response"):
            category = "model_routing"
        elif issue in ("context_loss", "memory_miss", "compaction_lost_context"):
            category = "memory_continuity"
        elif issue in ("repeated_mistake", "over_confirmation", "bad_routing"):
            category = "behavior_pattern"
        elif issue == "tool_error":
            category = "tool_reliability"
        else:
            category = "other"

        # Suggested action
        if category == "skill_gap":
            action = "Create or improve skill"
        elif category == "model_routing":
            action = "Update intelligent-router config"
        elif category == "memory_continuity":
            action = "Improve memory/heartbeat protocols"
        elif category == "behavior_pattern":
            action = "Update SOUL.md or AGENTS.md"
        elif category == "tool_reliability":
            action = "Add retry logic or fallback tools"
        else:
            action = "Investigate and address"

        sample_notes = [o["notes"] for o in group_outcomes if o.get("notes")][:3]

        patterns.append({
            "id": f"{task[:8]}-{issue[:8]}-{n}",
            "category": category,
            "task_type": task,
            "issue": issue,
            "frequency": n,
            "impact_score": round(impact, 4),
            "failure_rate": round(failure_rate, 3),
            "avg_quality": round(avg_quality, 2),
            "description": f"In '{task}' tasks, '{issue}' occurs {n}x with {failure_rate:.0%} failure rate",
            "sample_notes": sample_notes,
            "suggested_action": action,
        })

    # ── Sort by impact ─────────────────────────────────────────────────────────
    patterns.sort(key=lambda p: -p["impact_score"])

    # ── Overall health score ───────────────────────────────────────────────────
    total_success = sum(1 for o in outcomes if o.get("success"))
    overall_quality = sum(o.get("quality", 3) for o in outcomes) / len(outcomes)
    health_score = round((total_success / len(outcomes)) * (overall_quality / 5.0), 3)

    result = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "outcomes": len(outcomes),
            "days": days,
            "health_score": health_score,
        },
        "patterns": patterns[:20],  # top 20
    }

    # ── Save to disk ───────────────────────────────────────────────────────────
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PATTERNS_FILE, "w") as f:
        json.dump(result, f, indent=2)

    return result

def load_patterns() -> dict:
    if not PATTERNS_FILE.exists():
        return {}
    with open(PATTERNS_FILE) as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="RSI Analyzer - Detect improvement patterns")
    parser.add_argument("--days", type=int, default=7, help="Analysis window in days")
    parser.add_argument("--top", type=int, default=5, help="Show top N patterns")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    result = analyze(args.days)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    meta = result["meta"]
    patterns = result["patterns"]

    print(f"\n=== RSI Analysis: Last {meta['days']} days ===")
    print(f"Outcomes analyzed: {meta['outcomes']}")
    print(f"Health score: {meta.get('health_score', 'N/A')}")
    print(f"\nTop {min(args.top, len(patterns))} improvement patterns:\n")

    for i, p in enumerate(patterns[:args.top], 1):
        print(f"{i}. [{p['category'].upper()}] {p['description']}")
        print(f"   Impact: {p['impact_score']:.4f} | Fail rate: {p['failure_rate']:.0%} | Avg quality: {p['avg_quality']}/5")
        print(f"   Action: {p['suggested_action']}")
        if p["sample_notes"]:
            print(f"   Notes: {p['sample_notes'][0][:80]}")
        print()

    if not patterns:
        print("No patterns found. Keep logging outcomes with observer.py!")

if __name__ == "__main__":
    main()
