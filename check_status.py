#!/usr/bin/env python3
import requests
import json

COMFYUI_URL = "http://10.0.0.30:8188"
PROMPT_ID = "081def50-0e8f-42f6-a058-d648e1a289c4"

try:
    response = requests.get(f"{COMFYUI_URL}/api/history/{PROMPT_ID}")
    response.raise_for_status()
    history = response.json()

    print("History response:")
    print(json.dumps(history, indent=2))

except Exception as e:
    print(f"Error: {e}")
