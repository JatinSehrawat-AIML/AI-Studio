import os
import uuid
import torch
from diffusers import StableDiffusionPipeline

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

OUTPUT_DIR = "static/generated/scenes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MODEL_ID = "runwayml/stable-diffusion-v1-5"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"🧠 Loading Stable Diffusion on: {DEVICE.upper()}")

# --------------------------------------------------
# LOAD MODEL (ONCE)
# --------------------------------------------------

pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float32,          # ✅ safest
    use_safetensors=True,
    safety_checker=None                 # 🚀 disable for speed
).to(DEVICE)

pipe.set_progress_bar_config(disable=False)

# --------------------------------------------------
# PROMPT HELPERS
# --------------------------------------------------

def clamp_prompt(text: str, max_words=28):
    return " ".join(text.split()[:max_words])


def build_visual_prompt(slide: dict) -> str:
    title = slide.get("title", "")
    text = slide.get("text", "")

    prompt = f"""
Minimal modern cloud system illustration.
Soft pastel gradients.
Rounded shapes and smooth lines.
Abstract platform with connected modules.
Isometric flat design.
Clean tech SaaS style.
No text, no labels, no symbols.
"""
    return clamp_prompt(prompt)

# --------------------------------------------------
# IMAGE GENERATION
# --------------------------------------------------

def generate_slide_image(slide: dict) -> str:
    prompt = build_visual_prompt(slide)

    image_id = uuid.uuid4().hex
    output_path = os.path.join(OUTPUT_DIR, f"{image_id}.png")

    with torch.inference_mode():
        image = pipe(
            prompt=prompt,
            negative_prompt=(
                "photorealistic, people, faces, scenery, "
                "artistic illustration, logo, watermark, "
                "paragraph text, blurry text, noise"
            ),
            num_inference_steps=20,
            guidance_scale=6.5
        ).images[0]

    image.save(output_path)
    return f"/static/generated/scenes/{image_id}.png"

# --------------------------------------------------
# PUBLIC API
# --------------------------------------------------

def generate_images_for_slides(slides: list[dict]) -> list[str]:
    urls = []

    for slide in slides:
        try:
            urls.append(generate_slide_image(slide))
        except Exception as e:
            print("⚠️ Diffusion failed:", e)

    return urls
