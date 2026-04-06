#!/usr/bin/env python3
import requests
import json
import time
import os
from pathlib import Path

# Configuration
COMFYUI_URL = "http://10.0.0.30:8188"
OUTPUT_DIR = "/home/bowen/.openclaw/workspace/tmp"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "zimage_cover.png")

# The prompt ID from our previous submission
PROMPT_ID = "95eaec76-e222-4739-91a3-ccb4a01c07ea"

# Ensure output directory exists
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def wait_for_server(max_attempts=60):
    """Wait for the ComfyUI server to come back online"""
    print("Waiting for ComfyUI server to come back online...")
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{COMFYUI_URL}/api/system_stats", timeout=5)
            if response.status_code == 200:
                print(f"Server is back online after {attempt * 10} seconds")
                return True
        except:
            pass

        elapsed = (attempt + 1) * 10
        print(f"  [{elapsed}s] Server not responding yet...")
        time.sleep(10)

    print(f"Server did not come back online after {max_attempts * 10} seconds")
    return False

def check_prompt_history(prompt_id):
    """Check the history of a specific prompt"""
    try:
        print(f"Checking history for prompt: {prompt_id}")
        response = requests.get(f"{COMFYUI_URL}/api/history/{prompt_id}", timeout=10)
        response.raise_for_status()
        history = response.json()

        if prompt_id in history:
            prompt_data = history[prompt_id]
            print(f"Prompt found in history!")
            print(json.dumps(prompt_data, indent=2, default=str)[:500])
            return prompt_data
        else:
            print(f"Prompt {prompt_id} not found in history")
            return None
    except Exception as e:
        print(f"Error checking history: {e}")
        return None

def download_image(image_info):
    """Download the generated image"""
    print("Downloading image...")
    try:
        filename = image_info.get("filename")
        subfolder = image_info.get("subfolder", "")

        # Construct the download URL
        if subfolder:
            download_url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type=output"
        else:
            download_url = f"{COMFYUI_URL}/view?filename={filename}&type=output"

        print(f"Download URL: {download_url}")

        response = requests.get(download_url, timeout=60)
        response.raise_for_status()

        # Save the image
        with open(OUTPUT_FILE, "wb") as f:
            f.write(response.content)

        print(f"Image saved to: {OUTPUT_FILE}")
        return True

    except Exception as e:
        print(f"Error downloading image: {e}")
        return False

def main():
    print("="*60)
    print("ComfyUI Recovery Tool")
    print("="*60)
    print(f"Looking for prompt ID: {PROMPT_ID}")
    print()

    # Wait for server
    if not wait_for_server():
        print("\nFailed to reconnect to ComfyUI server")
        return False

    print()

    # Check history
    prompt_data = check_prompt_history(PROMPT_ID)
    if not prompt_data:
        print("Prompt data not found")
        return False

    print()

    # Try to extract outputs
    if "outputs" in prompt_data:
        outputs = prompt_data["outputs"]
        if "9" in outputs and "images" in outputs["9"]:
            images = outputs["9"]["images"]
            if images:
                print(f"Found {len(images)} image(s) in prompt output")
                image_info = images[0]
                if download_image(image_info):
                    print()
                    print("="*60)
                    print("SUCCESS!")
                    print(f"Image recovered and saved to: {OUTPUT_FILE}")
                    print("="*60)
                    return True

    print("No images found in prompt output")
    return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
