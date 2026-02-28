import requests, json

def upscale_image(input_filename, output_prefix):
    workflow = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": input_filename}
        },
        "2": {
            "class_type": "UpscaleModelLoader",
            "inputs": {"model_name": "RealESRGAN_x4plus.pth"}
        },
        "3": {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {
                "upscale_model": ["2", 0],
                "image": ["1", 0]
            }
        },
        "4": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["3", 0],
                "filename_prefix": output_prefix
            }
        }
    }
    resp = requests.post("http://localhost:8188/prompt", json={"prompt": workflow})
    return resp.json()

r1 = upscale_image("mbd_cover_deepseek_v2_00001_.png", "mbd_cover_deepseek_4k")
print("DeepSeek 4K:", r1)

r2 = upscale_image("mbd_cover_resume_v2_00001_.png", "mbd_cover_resume_4k")
print("Resume 4K:", r2)

r3 = upscale_image("mbd_cover_xiaohongshu_v2_00001_.png", "mbd_cover_xiaohongshu_4k")
print("XHS 4K:", r3)
