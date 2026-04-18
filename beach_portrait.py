import requests

workflow = {
    "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image"}},
    "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": "photorealistic portrait of a beautiful Asian woman in her 30s, walking on a sunny tropical beach, facing camera, warm smile, long black hair blowing in sea breeze, wearing a light flowy summer dress, shallow depth of field, golden hour lighting, waves behind her, sand and ocean background, 85mm lens, f/1.8 bokeh, professional photography, ultra detailed skin texture, 8K"}},
    "3": {"class_type": "EmptyLatentImage", "inputs": {"width": 832, "height": 1216, "batch_size": 1}},
    "4": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
    "5": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 3.0}},
    "6": {"class_type": "KSampler", "inputs": {
        "model": ["5", 0], "positive": ["2", 0], "negative": ["7", 0],
        "latent_image": ["3", 0], "seed": 5678, "steps": 28,
        "cfg": 4.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
    }},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": "cartoon, anime, illustration, painting, blurry, low quality, watermark, text, deformed, ugly, unrealistic, 3D render, plastic skin, oversaturated, bad anatomy, extra limbs"}},
    "8": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "9": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["8", 0]}},
    "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "beach_portrait"}}
}

resp = requests.post("http://localhost:8188/prompt", json={"prompt": workflow})
print("Beach portrait:", resp.json())
