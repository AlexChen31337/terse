#!/usr/bin/env python3
"""
memory-security: scan_memory.py
Scans text for prompt injection, exfiltration, invisible Unicode, and credential patterns.
Returns JSON verdict.

Usage:
    uv run python scripts/scan_memory.py --text "content to scan"
    echo "content" | uv run python scripts/scan_memory.py
"""

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
PATTERNS_FILE = SKILL_DIR / "references" / "patterns.json"

SEVERITY_MAP = {
    "prompt_injection": "critical",
    "exfiltration": "critical",
    "invisible_unicode": "high",
    "credential_patterns": "high",
}


def load_patterns() -> dict:
    with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def scan_text(text: str, patterns: dict) -> list[dict]:
    findings = []
    for category, cat_data in patterns.items():
        # Support both flat list and nested {severity, patterns} format
        if isinstance(cat_data, dict):
            pattern_list = cat_data.get("patterns", [])
            severity = cat_data.get("severity", SEVERITY_MAP.get(category, "low"))
        else:
            pattern_list = cat_data
            severity = SEVERITY_MAP.get(category, "low")
        for raw_pattern in pattern_list:
            try:
                # For invisible_unicode patterns, handle escape sequences
                if category == "invisible_unicode":
                    # Convert JSON unicode escape to actual character for matching
                    actual_char = raw_pattern.encode("utf-8").decode("unicode_escape")
                    if actual_char in text:
                        findings.append({
                            "category": category,
                            "severity": severity,
                            "pattern": raw_pattern,
                            "match": repr(actual_char),
                        })
                else:
                    compiled = re.compile(raw_pattern, re.IGNORECASE | re.MULTILINE)
                    match = compiled.search(text)
                    if match:
                        matched_str = match.group(0)
                        # Truncate long matches
                        if len(matched_str) > 100:
                            matched_str = matched_str[:100] + "..."
                        findings.append({
                            "category": category,
                            "severity": severity,
                            "pattern": raw_pattern,
                            "match": matched_str,
                        })
            except re.error as e:
                # Log bad pattern but continue
                findings.append({
                    "category": category,
                    "severity": "error",
                    "pattern": raw_pattern,
                    "match": f"[pattern error: {e}]",
                })
    return findings


def compute_verdict(findings: list[dict]) -> str:
    severities = {f["severity"] for f in findings}
    if "critical" in severities:
        return "BLOCK"
    if "high" in severities:
        return "WARN"
    return "PASS"


def main():
    parser = argparse.ArgumentParser(
        description="Scan text for security threats before writing to memory."
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Text content to scan. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args()

    if args.text is not None:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    try:
        patterns = load_patterns()
    except FileNotFoundError:
        result = {
            "verdict": "ERROR",
            "findings": [{"category": "system", "severity": "error",
                          "pattern": "n/a", "match": f"patterns.json not found at {PATTERNS_FILE}"}],
        }
        print(json.dumps(result, indent=2 if args.pretty else None))
        sys.exit(2)

    findings = scan_text(text, patterns)
    verdict = compute_verdict(findings)

    result = {"verdict": verdict, "findings": findings}
    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))

    # Exit codes: 0=PASS, 1=WARN, 2=BLOCK, 3=ERROR
    exit_codes = {"PASS": 0, "WARN": 1, "BLOCK": 2, "ERROR": 3}
    sys.exit(exit_codes.get(verdict, 3))


if __name__ == "__main__":
    main()
