#!/usr/bin/env python3
"""Update lastSessionId in heartbeat-state.json"""
import json
import sys
import os

STATE_FILE = "/home/bowen/clawd/memory/heartbeat-state.json"

new_id = sys.argv[1] if len(sys.argv) > 1 else ""
if not new_id:
    print("Usage: update_session_id.py <session-id>")
    sys.exit(1)

try:
    with open(STATE_FILE) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {}

data["lastSessionId"] = new_id

with open(STATE_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"Updated lastSessionId to: {new_id}")
