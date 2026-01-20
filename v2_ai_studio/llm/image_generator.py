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

# 🔒 FP32 for maximum stability
DTYPE = torch.float32

print(f"🧠 Loading Runway SD 1.5 on: {DEVICE.upper()} (HYBRID MODE)")

# --------------------------------------------------
# LAZY PIPELINE (reload-safe)
# --------------------------------------------------

_pipe = None

def get_pipe():
    global _pipe
    if _pipe is None:
        _pipe = StableDiffusionPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=DTYPE,
            use_safetensors=True
        ).to(DEVICE)

        # Stability + memory
        _pipe.enable_attention_slicing()
        _pipe.set_progress_bar_config(disable=False)

    return _pipe

# --------------------------------------------------
# HYBRID BACKGROUND PROMPT
# --------------------------------------------------

def build_background_prompt() -> str:
    """
    Pure background image prompt.
    NO semantic meaning, NO text, NO diagrams.
    Designed to work with ANY PPT.
    """
    return (
        "Abstract educational background illustration, "
        "soft gradient colors, "
        "minimal geometric shapes, "
        "modern professional style, "
        "balanced composition, "
        "no text, no letters, no numbers, no symbols, "
        "no diagrams, no flowcharts, "
        "high quality, clean visual"
    )

# --------------------------------------------------
# IMAGE GENERATION
# --------------------------------------------------

def generate_slide_image() -> str:
    pipe = get_pipe()
    prompt = build_background_prompt()

    image_id = uuid.uuid4().hex
    output_path = os.path.join(OUTPUT_DIR, f"{image_id}.png")

    with torch.no_grad():
        result = pipe(
            prompt=prompt,
            negative_prompt=(
                "text, letters, numbers, symbols, "
                "logos, diagrams, charts, flowcharts, "
                "watermark, blurry, low quality"
            ),
            num_inference_steps=20,
            guidance_scale=6.0
        )

        image = result.images[0]

    image.save(output_path)
    return f"/static/generated/scenes/{image_id}.png"

# --------------------------------------------------
# PUBLIC API (HYBRID)
# --------------------------------------------------

def generate_images_for_slides(slides: list[dict]) -> list[str]:
    """
    Hybrid mode:
    - One abstract background per slide
    - Images are NOT responsible for meaning
    """
    return [generate_slide_image() for _ in slides]
