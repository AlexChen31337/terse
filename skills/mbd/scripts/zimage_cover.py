#!/usr/bin/env python3
"""
ZImage Book Cover Generator
Generates a book cover via ComfyUI ZImage on the GPU server (peter@10.0.0.44),
SCPs the result back, uploads to imgbb or returns local path.

Usage:
  uv run python zimage_cover.py --title "AI教你躺平" --topic "AI副业" [--output /tmp/cover.png]
"""

import argparse
import base64
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path

GPU_HOST = "peter@10.0.0.44"
GPU_SSH_KEY = str(Path.home() / ".ssh/id_ed25519_alexchen")
COMFYUI_PORT = 8188
COMFYUI_API = f"http://localhost:{COMFYUI_PORT}"

# ── Cover prompt templates per topic ────────────────────────────────────────
COVER_PROMPTS = {
    "AI副业": (
        "Cyberpunk Chinese entrepreneur lying on a floating cloud of cash, "
        "surrounded by glowing AI holograms and digital yuan symbols, "
        "neon city skyline, lofi aesthetic, relaxed and wealthy vibe, "
        "cinematic lighting, 9:16 portrait"
    ),
    "提示词": (
        "Ancient Chinese scroll unrolling to reveal glowing AI prompt text, "
        "golden light emanating from digital characters, mystical alchemy lab "
        "with circuit board elements, cyberpunk meets traditional Chinese art, "
        "dramatic cinematic atmosphere, 9:16 portrait"
    ),
    "职场": (
        "Futuristic office in Shanghai 2026, robot and human working side by side, "
        "one looking stressed the other relaxed, neon signs in Chinese characters, "
        "cinematic dramatic lighting, dystopian corporate aesthetic, 9:16 portrait"
    ),
    "区块链": (
        "Cyberpunk Chinese hacker in a hoodie, floating blockchain nodes and "
        "crypto coins orbiting around them, holographic DeFi dashboards, "
        "electric blue and gold color scheme, rain-soaked neon city, 9:16 portrait"
    ),
    "恋爱": (
        "Romantic scene with AI cupid made of circuits shooting digital arrows, "
        "couple texting with AI speech bubbles, warm neon bokeh background, "
        "pastel cyberpunk aesthetic, heartbeat waveform, 9:16 portrait"
    ),
    "理财": (
        "Chinese investor sitting in a lotus position above a rising Bitcoin chart, "
        "AI robot advisor whispering in their ear, gold coins and candlestick charts "
        "floating in the air, serene yet wealthy atmosphere, cinematic, 9:16 portrait"
    ),
    "写作": (
        "Magical typewriter made of glowing circuit boards typing Chinese characters "
        "that fly off the page as butterflies, infinite library background, "
        "warm golden light, cyberpunk studio aesthetic, 9:16 portrait"
    ),
    "default": (
        "Futuristic Chinese person lying on a digital cloud, AI assistant hologram "
        "beside them, city skyline with neon Chinese characters, relaxed wealthy "
        "aesthetic, cinematic dramatic lighting, 9:16 portrait"
    ),
}

NEGATIVE_PROMPT = (
    "blurry, low quality, deformed, watermark, text, ugly, oversaturated, "
    "bad anatomy, duplicate, western style, english text"
)


def get_cover_prompt(title: str, topic_hint: str) -> str:
    """Pick best prompt based on topic hint."""
    for key in COVER_PROMPTS:
        if key in topic_hint or key in title:
            return COVER_PROMPTS[key]
    return COVER_PROMPTS["default"]


def build_workflow(prompt: str, seed: int, filename_prefix: str) -> dict:
    """Build ComfyUI ZImage workflow JSON."""
    return {
        "1": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"
        }},
        "2": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "pixart"
        }},
        "3": {"class_type": "VAELoader", "inputs": {
            "vae_name": "z_image_ae.safetensors"
        }},
        "4": {"class_type": "CLIPTextEncode", "inputs": {
            "text": prompt, "clip": ["2", 0]
        }},
        "5": {"class_type": "CLIPTextEncode", "inputs": {
            "text": NEGATIVE_PROMPT, "clip": ["2", 0]
        }},
        "6": {"class_type": "EmptyLatentImage", "inputs": {
            "width": 768, "height": 1024, "batch_size": 1
        }},
        "7": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0],
            "seed": seed, "steps": 4, "cfg": 1.0,
            "sampler_name": "euler", "scheduler": "normal",
            "denoise": 1.0, "latent_image": ["6", 0]
        }},
        "8": {"class_type": "VAEDecode", "inputs": {
            "samples": ["7", 0], "vae": ["3", 0]
        }},
        "9": {"class_type": "SaveImage", "inputs": {
            "images": ["8", 0], "filename_prefix": filename_prefix
        }},
    }


def run_on_gpu_server(workflow: dict, filename_prefix: str, timeout: int = 120) -> str | None:
    """Submit workflow to ComfyUI on GPU server via SSH, return remote output path."""
    workflow_json = json.dumps({"prompt": workflow})
    
    script = f"""
import urllib.request, json, time

workflow_json = {repr(workflow_json)}
api = "http://localhost:{COMFYUI_PORT}"

# Submit prompt
req = urllib.request.Request(
    f"{{api}}/prompt",
    data=workflow_json.encode(),
    headers={{"Content-Type": "application/json"}},
    method="POST"
)
with urllib.request.urlopen(req, timeout=30) as r:
    resp = json.loads(r.read())

prompt_id = resp["prompt_id"]
print(f"Submitted: {{prompt_id}}")

# Poll until done
for _ in range({timeout}):
    time.sleep(1)
    with urllib.request.urlopen(f"{{api}}/history/{{prompt_id}}", timeout=10) as r:
        hist = json.loads(r.read())
    if prompt_id in hist:
        outputs = hist[prompt_id].get("outputs", {{}})
        for node_id, node_out in outputs.items():
            if "images" in node_out:
                img = node_out["images"][0]
                path = f"/data2/comfyui/ComfyUI/output/{{img['filename']}}"
                print(f"OUTPUT:{{path}}")
                exit(0)

print("TIMEOUT")
exit(1)
"""
    
    result = subprocess.run(
        ["ssh", "-i", GPU_SSH_KEY, "-o", "ConnectTimeout=10",
         "-o", "StrictHostKeyChecking=no", GPU_HOST,
         f"python3 -c {repr(script)}"],
        capture_output=True, text=True, timeout=timeout + 30
    )
    
    if result.returncode != 0:
        print(f"⚠️ GPU server error: {result.stderr[:200]}", file=sys.stderr)
        return None
    
    for line in result.stdout.splitlines():
        if line.startswith("OUTPUT:"):
            return line[7:].strip()
    
    return None


def scp_from_gpu(remote_path: str, local_path: str) -> bool:
    """SCP file from GPU server to local."""
    result = subprocess.run(
        ["scp", "-i", GPU_SSH_KEY, "-o", "StrictHostKeyChecking=no",
         f"{GPU_HOST}:{remote_path}", local_path],
        capture_output=True, text=True, timeout=60
    )
    return result.returncode == 0


def upload_to_imgbb(image_path: str) -> str | None:
    """Upload image to imgbb (free, no API key needed for base64 upload)."""
    # Try imgbb free upload
    IMGBB_KEY = os.environ.get("IMGBB_API_KEY", "")
    if not IMGBB_KEY:
        return None
    
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    
    data = f"key={IMGBB_KEY}&image={urllib.parse.quote(b64)}"
    try:
        req = urllib.request.Request(
            "https://api.imgbb.com/1/upload",
            data=data.encode(),
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        if resp.get("success"):
            return resp["data"]["url"]
    except Exception:
        pass
    return None


def upload_to_mbd(image_path: str, mbd_token: str) -> str | None:
    """Try to upload to MbD's CDN (if upload endpoint exists)."""
    # MbD doesn't expose image upload in current docs — skip
    return None


def generate_cover(title: str, topic_hint: str, output_path: str | None = None,
                   mbd_token: str | None = None) -> str | None:
    """
    Full pipeline: generate → SCP → upload → return public URL or local path.
    Returns: public image URL if uploadable, else local file path, else None.
    """
    print(f"🎨 Generating ZImage cover for 《{title}》...")
    
    prompt = get_cover_prompt(title, topic_hint)
    seed = random.randint(1, 999999)
    prefix = f"mbd_cover_{int(time.time())}"
    
    workflow = build_workflow(prompt, seed, prefix)
    
    # Run on GPU server
    print(f"   Submitting to ComfyUI (seed={seed})...")
    remote_path = run_on_gpu_server(workflow, prefix, timeout=90)
    if not remote_path:
        print("❌ Image generation failed or timed out", file=sys.stderr)
        return None
    
    print(f"   ✅ Generated: {remote_path}")
    
    # SCP back
    if output_path is None:
        output_path = f"/tmp/{prefix}.png"
    
    print(f"   Downloading to {output_path}...")
    if not scp_from_gpu(remote_path, output_path):
        print("❌ SCP failed", file=sys.stderr)
        return None
    
    print(f"   ✅ Downloaded ({Path(output_path).stat().st_size // 1024}KB)")
    
    # Try to upload to get a public URL
    url = upload_to_imgbb(output_path)
    if url:
        print(f"   ✅ Uploaded: {url}")
        return url
    
    # Return local path as fallback (caller must handle hosting)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="ZImage Book Cover Generator")
    parser.add_argument("--title", required=True, help="Book title (Chinese)")
    parser.add_argument("--topic", default="", help="Topic hint for prompt selection")
    parser.add_argument("--output", default=None, help="Local output path")
    parser.add_argument("--mbd-token", default=None, help="MbD token for upload")
    args = parser.parse_args()
    
    result = generate_cover(args.title, args.topic, args.output, args.mbd_token)
    if result:
        print(f"\n✅ Cover ready: {result}")
    else:
        print("\n❌ Cover generation failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
