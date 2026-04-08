# TOOLS.md - Local Notes

## SSH Hosts

### GPU Server
- **Host:** `peter@10.0.0.30` | **Key:** `~/.ssh/id_ed25519_alexchen`
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

## Local Inference Stack (Dell XPS RTX 3070)
- **llama.cpp:** Built at `/tmp/llama.cpp/build/bin/` with CUDA+FA (arch 86)
- **Ollama v0.20.0:** Installed, `ollama run gemma4:26b` (~1.5 tok/s CPU-heavy)
- **Models registered in Ollama:**
  - `gemma4:26b` (17GB MoE)
  - `opus-qwen35:q3km` (15.6GB MoE, 3.5 tok/s)
  - `opus-qwen9b:q5km` (6.1GB dense,25+ tok/s full GPU)
- **Custom GGUFs (proper tokenizer):**
  - `/data/models/qwen9b-opus-Q5_K_M.gguf` (llama.cpp, 5.0s with <tool_call>tag)
  - `/data/models/qwen9b-opus-distilled-Q5_K_M.gguf` (broken tokenizer)
- **Prompt template for thinking models:** must `<tool_call>tag after `<|im_start|>assistant\n` in prompt
- **CUDA 12.0** installed via `nvidia-cuda-toolkit`
- **GPU server (10.0.0.30):** RTX 3090 + 3080 + 2070S = 42GB total
- **Dell XPS sudo:** `bowen@2025` (encrypted at `memory/encrypted/local-sudo.enc`)

## Knowledge Base Skill
- **Skill dir:** `~/.openclaw/workspace/skills/knowledge-base/`
- **Repo:** https://github.com/AlexChen31337/llm-knowledge-base
- **Scripts:** ingest.py, compile.py, lint.py, search.py, serve.py
- **Status:** ✅ Wired into workspace

## Gemma 4 26B-A4B (Local)
- **Ollama v0.20.0:** `ollama run gemma4:26b` works (fixed tokenizer), ~1.5 tok/s CPU-heavy
- **llama.cpp:** Built at `/tmp/llama.cpp/build/bin/` with CUDA+FA (arch 86)
- **⚠️ Unsloth GGUFs broken** (bad tokenizer → garbage output). Wait for re-upload or use ggml-org official.
- **GPU server (10.0.0.30):** 3090 24GB = full Q4_K_M fits in VRAM. Ideal for fast inference.
- **Dell XPS sudo:** `bowen@2025` (encrypted at `memory/encrypted/local-sudo.enc`)
