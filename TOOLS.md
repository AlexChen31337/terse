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
  - `/data` — 110GB SSD (18GB free) — ComfyUI, existing models (⚠️ I/O errors, avoid writes)
  - `/data2` — 916GB USB HDD (870GB free) — new models, InfiniteTalk, 256GB swapfile
- **ComfyUI:** `/data/ai-stack/comfyui/ComfyUI/` (port 8188)
- **Models:**
  - `/data`: realistic_vision_v51, ltx-2-19b-distilled-fp8, Gemma-3, Z-Image
  - `/data2/ai-models/`: (new storage for InfiniteTalk, etc.)
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
