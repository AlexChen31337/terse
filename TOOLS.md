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
- **ComfyUI:** `/home/peter/ai-stack/comfyui/ComfyUI/`
- **Models:** `juggernautXL_v9.safetensors`, `sd_xl_turbo_1.0_fp16.safetensors`
- **Password backup:** encrypted in `memory/gpu-server-credentials.json.enc`

### Pi (Bloop-Eye)
- **Host:** `admin@192.168.99.25`
- **Key:** `~/.ssh/id_ed25519_alexchen`
- **Connect:** `ssh -i ~/.ssh/id_ed25519_alexchen admin@192.168.99.25`
- **Agent config:** `~/.evoclaw/agent.toml`

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
