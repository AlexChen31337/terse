#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from pathlib import Path

# Configuration
COMFYUI_URL = "http://10.0.0.30:8188"
API_ENDPOINT = f"{COMFYUI_URL}/api/prompt"
OUTPUT_DIR = "/home/bowen/.openclaw/workspace/tmp"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "zimage_cover.png")

# Ensure output directory exists
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# ComfyUI Workflow
workflow = {
    "1": {
        "inputs": {
            "ckpt_name": "z_image_turbo_bf16.safetensors"
        },
        "class_type": "CheckpointLoaderSimple",
        "_meta": {
            "title": "Load Checkpoint"
        }
    },
    "2": {
        "inputs": {
            "clip_name": "qwen_3_4b.safetensors",
            "type": "qwen_image"
        },
        "class_type": "CLIPLoader",
        "_meta": {
            "title": "Load CLIP"
        }
    },
    "3": {
        "inputs": {
            "vae_name": "ae.safetensors"
        },
        "class_type": "VAELoader",
        "_meta": {
            "title": "Load VAE"
        }
    },
    "4": {
        "inputs": {
            "text": "Futuristic digital bridge connecting glowing nodes, flow of luminous data streams between cloud infrastructure and autonomous agents, neural connections, cyberpunk aesthetic, vibrant blue and purple gradients, sleek modern technology, interconnected systems, ethereal glow, high quality digital art",
            "clip": ["2", 0]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "CLIP Text Encode (Positive)"
        }
    },
    "5": {
        "inputs": {
            "text": "text, letters, numbers, words, characters, fonts, typography, logo, title, subtitle, caption, label, sign, writing, watermark, blurry, low quality, deformed, ugly, extra limbs, cartoon, anime",
            "clip": ["2", 0]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "CLIP Text Encode (Negative)"
        }
    },
    "6": {
        "inputs": {
            "width": 768,
            "height": 1024,
            "length": 1,
            "batch_size": 1
        },
        "class_type": "EmptyLatentImage",
        "_meta": {
            "title": "Empty Latent Image"
        }
    },
    "7": {
        "inputs": {
            "seed": 42,
            "steps": 20,
            "cfg": 3.5,
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
            "positive": ["4", 0],
            "negative": ["5", 0],
            "latent_image": ["6", 0],
            "model": ["1", 0]
        },
        "class_type": "KSampler",
        "_meta": {
            "title": "KSampler"
        }
    },
    "8": {
        "inputs": {
            "samples": ["7", 0],
            "vae": ["3", 0]
        },
        "class_type": "VAEDecode",
        "_meta": {
            "title": "VAE Decode"
        }
    },
    "9": {
        "inputs": {
            "filename_prefix": "zimage_cover",
            "images": ["8", 0]
        },
        "class_type": "SaveImage",
        "_meta": {
            "title": "Save Image"
        }
    }
}

# Request format
request_payload = {
    "prompt": workflow,
    "client_id": "claude_code_client"
}

def submit_workflow():
    """Submit the workflow to ComfyUI"""
    print("Submitting workflow to ComfyUI...")
    print(f"Payload size: {len(json.dumps(request_payload))} bytes")
    try:
        response = requests.post(API_ENDPOINT, json=request_payload, timeout=30)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        data = response.json()
        print(f"Response Body: {json.dumps(data, indent=2)}")

        if response.status_code == 200:
            prompt_id = data.get("prompt_id")
            if prompt_id:
                print(f"SUCCESS: Workflow submitted with Prompt ID: {prompt_id}")
                return prompt_id

        return None
    except Exception as e:
        print(f"Error submitting workflow: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_history(prompt_id):
    """Get full history of a prompt"""
    try:
        response = requests.get(f"{COMFYUI_URL}/api/history/{prompt_id}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting history: {e}")
        return {}

def poll_completion(prompt_id, timeout=1800, poll_interval=5):
    """Poll for workflow completion"""
    print(f"Polling for completion (timeout: {timeout}s, poll interval: {poll_interval}s)...")
    start_time = time.time()
    last_status = None

    while time.time() - start_time < timeout:
        try:
            history = get_history(prompt_id)

            if not history:
                elapsed = time.time() - start_time
                if elapsed % 30 < poll_interval:  # Print every ~30 seconds
                    print(f"  [{elapsed:.1f}s] No history found yet, still waiting...")
                time.sleep(poll_interval)
                continue

            if prompt_id in history:
                prompt_data = history[prompt_id]

                # Print status details
                if "status" in prompt_data:
                    status = prompt_data["status"]
                    current_status = (status.get("status_str"), status.get("max"), status.get("value"))
                    if current_status != last_status:
                        print(f"  Status: {current_status}")
                        last_status = current_status

                # Check if outputs exist
                if "outputs" in prompt_data:
                    outputs = prompt_data["outputs"]
                    # Find SaveImage output (node 9)
                    if "9" in outputs and "images" in outputs["9"]:
                        images = outputs["9"]["images"]
                        if images:
                            print(f"Workflow completed! Found {len(images)} image(s)")
                            return images

                # Check for execution error
                if "status" in prompt_data:
                    status = prompt_data["status"]
                    if status.get("status_str") == "execution error":
                        print(f"Execution error detected: {status}")
                        return None

            elapsed = time.time() - start_time
            if int(elapsed) % 30 == 0:  # Print every 30 seconds
                print(f"  [{elapsed:.1f}s] Still processing...")
            time.sleep(poll_interval)

        except Exception as e:
            print(f"Error polling: {e}")
            time.sleep(poll_interval)

    print(f"Timeout waiting for completion after {timeout}s")
    # Try one last time to get the history
    final_history = get_history(prompt_id)
    print(f"Final history state: {json.dumps(final_history, indent=2)}")
    return None

def download_image(image_info, prompt_id):
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
    print("ComfyUI Cover Image Generator v2")
    print("="*60)
    print(f"Image dimensions: 768x1024")
    print(f"Model: z_image_turbo_bf16.safetensors")
    print(f"Steps: 20, CFG: 3.5")
    print(f"Sampler: euler/simple")
    print(f"Seed: 42")
    print("="*60 + "\n")

    # Submit workflow
    prompt_id = submit_workflow()
    if not prompt_id:
        print("Failed to submit workflow")
        return False

    print()  # Blank line for readability

    # Poll for completion
    images = poll_completion(prompt_id)
    if not images:
        print("Failed to get workflow outputs")
        return False

    print()  # Blank line for readability

    # Download image
    if images:
        image_info = images[0]
        success = download_image(image_info, prompt_id)
        if success:
            print("="*60)
            print("SUCCESS!")
            print(f"Cover image generated and saved to:")
            print(f"  {OUTPUT_FILE}")
            print("="*60)
            return True
        else:
            print("Failed to download image")
            return False
    else:
        print("No images in output")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
