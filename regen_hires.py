import json, requests

def queue_image(prompt_text, filename_prefix, seed, width=1024, height=1536, steps=20):
    workflow = {
        "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image"}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": prompt_text}},
        "3": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "4": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "5": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 3.0}},
        "6": {"class_type": "KSampler", "inputs": {
            "model": ["5", 0], "positive": ["2", 0], "negative": ["7", 0],
            "latent_image": ["3", 0], "seed": seed, "steps": steps,
            "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
        }},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": "blurry low quality watermark text"}},
        "8": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["8", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": filename_prefix}}
    }
    resp = requests.post("http://localhost:8188/prompt", json={"prompt": workflow})
    return resp.json()

r2 = queue_image(
    "professional business book cover, resume document flying out of laptop screen transforming into golden light particles, modern CBD skyscrapers background, hopeful atmosphere, blue and gold color scheme, ultra detailed photorealistic 8K",
    "mbd_cover_resume_v2", 2222, width=1024, height=1536, steps=20
)
print("Resume v2:", r2)

r3 = queue_image(
    "vibrant trendy book cover, smartphone screen showing social media feed with follower count skyrocketing, golden coins and hearts floating around, pink orange gradient background, cute modern kawaii style, ultra detailed 8K",
    "mbd_cover_xiaohongshu_v2", 3333, width=1024, height=1536, steps=20
)
print("XHS v2:", r3)
