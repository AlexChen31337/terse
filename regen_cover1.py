import requests

workflow = {
    "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image"}},
    "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": "futuristic Chinese tech book cover, DeepSeek AI blue theme, digital rain matrix effect, RMB yuan symbols intertwined with glowing AI code, dramatic neon lighting, cinematic, ultra detailed 8K, 1024x1536 portrait"}},
    "3": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1536, "batch_size": 1}},
    "4": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
    "5": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 3.0}},
    "6": {"class_type": "KSampler", "inputs": {
        "model": ["5", 0], "positive": ["2", 0], "negative": ["7", 0],
        "latent_image": ["3", 0], "seed": 4444, "steps": 20,
        "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
    }},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": "blurry low quality watermark typo misspelled text Depseek"}},
    "8": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "9": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["8", 0]}},
    "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "mbd_cover_deepseek_v2"}}
}

resp = requests.post("http://localhost:8188/prompt", json={"prompt": workflow})
print("DeepSeek v2:", resp.json())
