from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.script_service import generate_script_from_file
from llm.image_generator import generate_images_for_slides
from tts.audio_generator import script_to_audio

import os
import uuid
import re
import json

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

SLIDE_HEADER_RE = re.compile(r"^slide\s+(\d+)\s*:?", re.IGNORECASE)


def parse_slides_from_script(script: str) -> list[dict]:
    """
    Robust slide parser.
    Splits slides even if 'Slide X' appears mid-paragraph.
    """

    pattern = re.compile(r"(Slide\s+\d+\s*:?)", re.IGNORECASE)
    parts = pattern.split(script)

    slides = []
    current_title = None
    current_text = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if pattern.match(part):
            if current_title:
                slides.append({
                    "title": current_title,
                    "text": " ".join(current_text).strip()
                })
            current_title = part if part.endswith(":") else part + ":"
            current_text = []
        else:
            current_text.append(part)

    if current_title:
        slides.append({
            "title": current_title,
            "text": " ".join(current_text).strip()
        })

    # Safety fallback
    if not slides:
        slides = [{
            "title": "Slide 1:",
            "text": script.strip()
        }]

    return slides

def assign_slide_timings(slides: list[dict], duration: float):
    per_slide = duration / max(len(slides), 1)
    t = 0.0

    for idx, slide in enumerate(slides):
        slide["start"] = round(t, 2)
        slide["end"] = round(t + per_slide, 2)
        slide["slide_index"] = idx
        t += per_slide


def attach_words_to_slides(slides: list[dict], words: list[dict]):
    word_idx = 0

    for slide in slides:
        slide_words = []

        while word_idx < len(words):
            w = words[word_idx]

            if slide["start"] <= w["start"] <= slide["end"]:
                slide_words.append(w)
                word_idx += 1
            elif w["start"] > slide["end"]:
                break
            else:
                word_idx += 1

        slide["words"] = slide_words


# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# --------------------------------------------------
# 1️⃣ SCRIPT + IMAGE GENERATION (SLOW, ONE TIME)
# --------------------------------------------------

@router.post("/ui/generate", response_class=HTMLResponse)
async def generate_script_ui(
    request: Request,
    file: UploadFile = File(...)
):
    filename = file.filename.lower()

    if not filename.endswith((".pdf", ".pptx")):
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "Only PDF and PPTX files are supported."
            }
        )

    file_path = os.path.join(
        UPLOAD_DIR,
        f"{uuid.uuid4()}_{file.filename}"
    )

    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        script = generate_script_from_file(file_path)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    if not script.strip():
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "Failed to extract script from file."
            }
        )

    slides = parse_slides_from_script(script)

    # 🔥 IMAGE GENERATION (ONLY ONCE)
    try:
        image_urls = generate_images_for_slides(slides)
    except Exception as e:
        print("⚠️ Image generation failed:", e)
        image_urls = []

    for slide, img in zip(slides, image_urls):
        slide["image"] = img

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "script": script,
            "slides_json": json.dumps(slides)
        }
    )


# --------------------------------------------------
# 2️⃣ AUDIO ONLY (FAST)
# --------------------------------------------------

@router.post("/ui/audio", response_class=HTMLResponse)
def generate_audio_ui(
    request: Request,
    script: str = Form(...),
    slides_json: str = Form(...)
):
    if not script.strip():
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "Script is empty."
            }
        )

    slides = json.loads(slides_json)

    audio_result = script_to_audio(script)

    audio_url = audio_result["audio_url"]
    duration = audio_result["duration"]
    words = audio_result["timestamps"]

    assign_slide_timings(slides, duration)
    attach_words_to_slides(slides, words)

    return templates.TemplateResponse(
        "player.html",
        {
            "request": request,
            "audio_url": audio_url,
            "slides": slides
        }
    )
