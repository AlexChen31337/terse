#!/usr/bin/env python3
import subprocess
import json
import time
from datetime import datetime
import argparse

# Config
LABS = [
    "OpenAI", "AnthropicAI", "GoogleDeepMind", 
    "MetaAI", "MistralAI", "xai", "huggingface"
]
PEOPLE = [
    "karpathy", "ylecun", "sama", "demishassabis", 
    "gdb", "sawyerhood", "natfriedman", "IntuitMachine"
]
KEYWORDS = [
    "SOTA", "release", "benchmark", "weights", "open source", 
    "Llama", "GPT", "Claude", "Gemini", "DeepSeek", "Mistral",
    "coding", "agent"
]

def run_bird_search(query, count=3):
    """Run bird search and return raw output"""
    try:
        cmd = ["bird", "search", query, "-n", str(count)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error searching {query}: {result.stderr}"
        return result.stdout.strip()
    except Exception as e:
        return f"Failed to execute bird: {str(e)}"

def format_report(findings):
    """Format findings into a clean report"""
    print("\n\033[1m🤖 LLM Landscape Monitor Report\033[0m")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    if not findings:
        print("No significant updates found.")
        return

    for category, items in findings.items():
        if items:
            print(f"\033[1m{category}\033[0m")
            for item in items:
                print(f"{item}")
            print()

def main():
    parser = argparse.ArgumentParser(description="Monitor LLM developments")
    parser.add_argument("--focus", help="Add a specific focus keyword filter")
    parser.add_argument("--hours", type=int, default=24, help="Look back period (informational only for now)")
    args = parser.parse_args()

    findings = {"Labs": [], "People": []}
    
    print(f"Scanning {len(LABS)} labs and {len(PEOPLE)} researchers...")

    # Scan Labs
    for lab in LABS:
        out = run_bird_search(f"from:{lab}", count=2)
        if out and "No results" not in out:
            # Simple check for keywords in output (crude but effective filter)
            relevant = False
            for kw in KEYWORDS:
                if kw.lower() in out.lower():
                    relevant = True
                    break
            
            if relevant or args.focus:
                # If focus is set, strictly filter
                if args.focus and args.focus.lower() not in out.lower():
                    continue
                findings["Labs"].append(f"@{lab}:\n{out}\n")
            elif relevant:
                 findings["Labs"].append(f"@{lab}:\n{out}\n")

    # Scan People (stricter filter)
    for person in PEOPLE:
        out = run_bird_search(f"from:{person}", count=2)
        if out and "No results" not in out:
            relevant = False
            for kw in KEYWORDS:
                if kw.lower() in out.lower():
                    relevant = True
                    break
            
            if relevant:
                findings["People"].append(f"@{person}:\n{out}\n")

    format_report(findings)

if __name__ == "__main__":
    main()
