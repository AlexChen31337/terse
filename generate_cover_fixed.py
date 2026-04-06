#!/usr/bin/env python3
import requests
import json
import time
import os
from pathlib import Path

# Configuration
COMFYUI_URL = "http://10.0.0.30:8188"
API_ENDPOINT = f"{COMFYUI_URL}/api/prompt"
OUTPUT_DIR = "/home/bowen/.openclaw/workspace/tmp"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "zimage_cover.png")

# Ensure output directory exists
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# ComfyUI Workflow - the workflow itself is the prompt
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

# Request format: the prompt field contains the workflow
request_payload = {
    "prompt": workflow
}

def submit_workflow():
    """Submit the workflow to ComfyUI"""
    print("Submitting workflow to ComfyUI...")
    try:
        response = requests.post(API_ENDPOINT, json=request_payload)
        response.raise_for_status()
        data = response.json()
        prompt_id = data.get("prompt_id")
        if prompt_id:
            print(f"Workflow submitted successfully. Prompt ID: {prompt_id}")
            return prompt_id
        else:
            print("Error: No prompt ID in response")
            print(f"Response: {data}")
            return None
    except Exception as e:
        print(f"Error submitting workflow: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response text: {e.response.text}")
        return None

def poll_completion(prompt_id, timeout=600, poll_interval=2):
    """Poll for workflow completion"""
    print(f"Polling for completion (timeout: {timeout}s)...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{COMFYUI_URL}/api/history/{prompt_id}")
            response.raise_for_status()
            history = response.json()

            if prompt_id in history:
                prompt_data = history[prompt_id]

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
                        print(f"Execution error: {status}")
                        return None

            elapsed = time.time() - start_time
            print(f"  [{elapsed:.1f}s] Waiting for completion...")
            time.sleep(poll_interval)

        except Exception as e:
            print(f"Error polling: {e}")
            time.sleep(poll_interval)

    print(f"Timeout waiting for completion after {timeout}s")
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

        response = requests.get(download_url)
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
    print("ComfyUI Cover Image Generator")
    print("="*60)
    print(f"Image dimensions: 768x1024")
    print(f"Model: z_image_turbo_bf16.safetensors")
    print(f"Steps: 20, CFG: 3.5")
    print(f"Sampler: euler/simple")
    print(f"Seed: 42")
    print("="*60)

    # Submit workflow
    prompt_id = submit_workflow()
    if not prompt_id:
        print("Failed to submit workflow")
        return

    # Poll for completion (extended timeout for model loading)
    images = poll_completion(prompt_id, timeout=1800)
    if not images:
        print("Failed to get workflow outputs")
        return

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
        else:
            print("Failed to download image")
    else:
        print("No images in output")

if __name__ == "__main__":
    main()
