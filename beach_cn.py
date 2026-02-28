import requests

workflow = {
    "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image"}},
    "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": "一张超逼真的东亚成熟女性照片，站在阳光明媚的海滩上，面向镜头，肌肤自然光滑，乌黑亮丽长发随海风飘动，笑容甜美自然，穿着轻盈飘逸的夏日连衣裙，背景是蔚蓝的大海和金色沙滩，环境光线温暖柔和，营造出电影般的肖像效果。照片采用浅景深，双眼细节丰富，8K超高清分辨率，照片级真实感，专业摄影，面部细节极其清晰，构图完美，背景虚化柔和，时尚大片风格"}},
    "3": {"class_type": "EmptyLatentImage", "inputs": {"width": 832, "height": 1216, "batch_size": 1}},
    "4": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
    "5": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 3.0}},
    "6": {"class_type": "KSampler", "inputs": {
        "model": ["5", 0], "positive": ["2", 0], "negative": ["7", 0],
        "latent_image": ["3", 0], "seed": 9999, "steps": 28,
        "cfg": 4.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
    }},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": "模糊，低质量，卡通，动漫，插画，水印，文字，变形，丑陋，不真实，塑料感皮肤，过度饱和"}},
    "8": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "9": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["8", 0]}},
    "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "beach_cn"}}
}

resp = requests.post("http://localhost:8188/prompt", json={"prompt": workflow})
print("Beach CN:", resp.json())
