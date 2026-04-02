# TOOLS.md - Local Notes

## SSH Hosts

### GPU Server
- **Host:** `peter@10.0.0.44` | **Key:** `~/.ssh/id_ed25519_alexchen`
- **Sudo:** `peter@2025` | **GPUs:** 3090 (24GB), 3080 (10GB), 2070S (8GB) = 42GB total
- **RAM:** 16GB + 256GB swap on /data2 | **Storage:** /data (SSD), /data2 (916GB HDD)
- **ComfyUI:** `/data2/comfyui/ComfyUI/` port 8188, output at `/data2/comfyui/ComfyUI/output/`

### Pi (Bloop-Eye)
- **Host:** `admin@192.168.99.188` | **Key:** `~/.ssh/id_ed25519_alexchen`

## ZImage / ComfyUI
- **Model:** z_image_turbo_bf16.safetensors | **CLIP:** qwen_3_4b.safetensors (type: qwen_image) | **VAE:** ae.safetensors
- **Defaults:** Steps 20, CFG 3.5, euler/simple, cover 768×1024
- **Negative prompt (ALWAYS):** `text, letters, numbers, words, characters, fonts, typography, logo, title, subtitle, caption, label, sign, writing, watermark, blurry, low quality, deformed, ugly, extra limbs, cartoon, anime`

## Twitter/X
- **AUTH_TOKEN:** `25472f65c86e1e2cc3cfa906e4681319dc056776`
- **CT0:** `0d42d73880783e42fd267f26fbf6b082374982e72d04b44459f6bd5cca0166f3fdad8f693e733f79c933a618ddae34d1d3b7855db0e9b775ff99caf1d8ca7d01e59e11035cb7fab0c1d02b1067eb2bb1`
- **Account:** @unoclaw / @AlexChen31337
- **Playwright:** Use `compose/tweet` URL, `.fill()` on textarea, 15s between tweets. Full script in `memory/tools-archive-2026-04-02.md`.

## Payhip
- **Account:** alex.chen31337@gmail.com / PayhipStore@2026p
- **Login selector:** `input[name="login"]` (NOT `input[name="email"]`)
- **Store:** https://payhip.com/AlexChen31337
- **Full script:** `memory/tools-archive-2026-04-02.md`

## Intelligent Router
- **Config:** `~/.openclaw/workspace/skills/intelligent-router/config.json`
- **Helper:** `uv run python skills/intelligent-router/scripts/spawn_helper.py --model-only "task"`

## Autoresearch Hardware
- Nemotron/Qwen autoresearch: RTX 3070 8GB ONLY (not GPU server)
- Qwen3.5-35B best: 29.899 tok/s (IQ2_XXS, n_gpu=27, phase 12)
