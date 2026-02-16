# LTX-2 Setup Status - 2026-02-16 14:08 AEDT

## ✅ Current Status: 90% Complete

### What's Working

1. **✅ ComfyUI Installed & Running**
   - Location: `/data2/comfyui/ComfyUI`
   - Port: 8188
   - Web UI: http://10.0.0.44:8188
   - GPU: RTX 3090 (25GB VRAM) detected
   - PyTorch 2.10.0 + CUDA 12.8

2. **✅ LTX-2 Custom Nodes Loaded**
   - 20 LTX-2 nodes available in ComfyUI
   - Key nodes: EmptyLTXVLatentVideo, LTXVImgToVideo, LTXAVTextEncoderLoader
   - Custom node symlink: `/data2/comfyui/ComfyUI/custom_nodes/LTX-2` → `/data2/ai-models/LTX-2`

3. **✅ Models Available**
   - LoRA model: `ltx-2-19b-distilled-lora-384.safetensors` (7.2GB) in `/data2/comfyui/ComfyUI/models/loras/`
   - Quantized model: `ltx-2-19b-dev-Q4_K_M.gguf` (4.2GB) in `/data2/ai-models/`

### Missing Components

1. **❌ Base LTX-2 Model (Critical)**
   - Need: Base diffusion model checkpoint
   - Current: Only have LoRA (fine-tune) and quantized version
   - LoRA requires base model to work
   - Location needed: `/data2/comfyui/ComfyUI/models/checkpoints/` or `/data2/comfyui/ComfyUI/models/diffusion_models/`

2. **❓ Text Encoder (Maybe Required)**
   - LTX-2 nodes include `LTXAVTextEncoderLoader`
   - Directories empty:
     - `/data2/comfyui/ComfyUI/models/text_encoders/`
     - `/data2/ai-models/text_encoders/`
   - May need: Gemma 3 or T5 text encoder

### Available Models in /data2/ai-models

```
/data2/ai-models/
├── LTX-2/           (3.8MB - repository with custom nodes)
├── ltx-2-19b-dev-Q4_K_M.gguf  (4.2GB - quantized, may not be ComfyUI-compatible)
├── infinitetalk/    (49GB)
├── checkpoints/     (empty)
├── text_encoders/   (empty)
└── video_models/    (empty)
```

### What We Need to Download

**Option 1: Official LTX-2 Weights from Hugging Face**
```bash
# Base model (required for LoRA)
huggingface-cli download Lightricks/LTX-Video --include "ltx_video_2b_v0.9.safetensors" --local-dir /data2/ai-models/LTX-2-weights/

# Text encoder (if needed)
huggingface-cli download google/gemma-2-2b-it --local-dir /data2/comfyui/ComfyUI/models/text_encoders/gemma-2-2b-it/
```

**Option 2: Check if quantized model can be used**
- The `ltx-2-19b-dev-Q4_K_M.gguf` might be usable if we convert it or if ComfyUI has GGUF support
- Unlikely to work directly in ComfyUI (GGUF is for llama.cpp-based inference)

### Next Steps

1. **Immediate (5-10 min):**
   - Authenticate to Hugging Face CLI
   - Download base LTX-2 model (~10-15GB)
   - Place in correct directory

2. **Test (5 min):**
   - Create simple video generation workflow
   - Test with text prompt
   - Verify output quality

3. **Optional:**
   - Download text encoder if generation fails
   - Test LoRA application
   - Test image-to-video mode

### Current Blockers

1. **Missing base model** — Can't test video generation without it
2. **HF authentication** — May need token for model downloads

### Time Estimate

- Download base model: 5-10 minutes (depends on connection)
- Test generation: 5 minutes
- **Total remaining:** 10-20 minutes

---

**Summary:** ComfyUI + LTX-2 nodes are ready, just need to download the base model to start generating videos. 🎥
