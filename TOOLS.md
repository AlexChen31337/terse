# TOOLS.md - Local Notes

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases  
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## SSH Hosts

### GPU Server
- **Host:** `peter@10.0.0.44`
- **Key:** `~/.ssh/id_ed25519_alexchen`
- **Connect:** `ssh -i ~/.ssh/id_ed25519_alexchen peter@10.0.0.44`
- **Sudo password:** `peter@2025` (stored in `memory/gpu-server-credentials.json`)
- **GPUs (3 total, 42GB VRAM):**
  - GPU 0: RTX 3090 (24GB) — primary, used by ComfyUI
  - GPU 1: RTX 3080 (10GB)
  - GPU 2: RTX 2070 SUPER (8GB)
- **RAM:** 16GB system memory + **256GB swapfile on /data2**
- **Storage:**
  - `/` (root, `/dev/sda2`) — 110GB SSD, 70GB used after cleanup — **⚠️ owned by root, need `sudo` to create dirs**
  - `/data` — empty directory ON the root SSD (not a separate mount), use `sudo` to create subdirs then `chown peter:peter`
  - `/data2` — 916GB USB HDD — ComfyUI at `/data2/comfyui/ComfyUI/`, 256GB swapfile, slow (~60MB/s read)
- **ComfyUI:** `/data2/comfyui/ComfyUI/` (port 8188), output at `/data2/comfyui/ComfyUI/output/`
- **ZImage models (as of 2026-02-25, migrating to SSD):**
  - Diffusion: `/data/comfyui/models/diffusion_models/z_image_turbo_bf16.safetensors` (12GB, symlinked from /data2)
  - CLIP: `/data/comfyui/models/text_encoders/qwen_3_4b_fp8_mixed.safetensors` (5.3GB, symlinked from /data2)
  - VAE: `/data/comfyui/models/vae/z_image_ae.safetensors` (320MB, symlinked from /data2)
- **Password backup:** encrypted in `memory/gpu-server-credentials.json.enc`

### Pi (Bloop-Eye)
- **Host:** `admin@192.168.99.188` (was .25, changed after reboot)
- **Key:** `~/.ssh/id_ed25519_alexchen`
- **Connect:** `ssh -i ~/.ssh/id_ed25519_alexchen admin@192.168.99.25`
- **Agent config:** `~/.evoclaw/agent.toml`

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## ZImage / ComfyUI Generation Rules

### Negative Prompt (ALWAYS include)
```
text, letters, numbers, words, characters, fonts, typography, logo, title, subtitle, caption, label, sign, writing, watermark, blurry, low quality, typo, misspelled text, garbled text, gibberish, illegible writing, deformed letters, wrong characters, deformed, ugly, extra limbs, cartoon, anime
```

**Key rule (updated 2026-03-03):** NO text in generated images — ever. Always include `text, letters, numbers, words, characters, fonts, typography, logo, title, subtitle, caption, label, sign, writing` in the negative prompt. Bowen's explicit instruction: images must be text-free.

### Workflow defaults (ZImage Turbo)
- Model: `z_image_turbo_bf16.safetensors` (on `/data` SSD)
- CLIP: `qwen_3_4b.safetensors`, type: `qwen_image`
- VAE: `ae.safetensors`
- Steps: 20, CFG: 3.5, sampler: euler, scheduler: simple
- Cover size: 768×1024
