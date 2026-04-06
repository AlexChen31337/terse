#!/usr/bin/env python3
import requests
import json

COMFYUI_URL = "http://10.0.0.30:8188"
API_ENDPOINT = f"{COMFYUI_URL}/api/prompt"

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

try:
    print("Submitting workflow...")
    print("Workflow JSON:")
    print(json.dumps(workflow, indent=2))
    print("\n" + "="*60)

    response = requests.post(API_ENDPOINT, json=workflow)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")

except Exception as e:
    print(f"Error: {e}")
