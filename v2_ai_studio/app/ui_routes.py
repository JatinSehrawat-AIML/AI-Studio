from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

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

def parse_slides_from_script(script: str) -> list[dict]:
    """
    Strict slide parser.
    Only splits on lines that START with 'Slide X:'.
    """
    lines = script.splitlines()

    slides = []
    current_title = None
    current_text = []

    header_pattern = re.compile(r"^Slide\s+(\d+)\s*:\s*$", re.IGNORECASE)

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if header_pattern.match(line):
            # Save previous slide
            if current_title:
                slides.append({
                    "title": current_title,
                    "text": " ".join(current_text).strip()
                })

            current_title = line
            current_text = []
        else:
            current_text.append(line)

    # Last slide
    if current_title:
        slides.append({
            "title": current_title,
            "text": " ".join(current_text).strip()
        })

    # Fallback if no headers detected
    if not slides:
        slides = [{
            "title": "Slide 1:",
            "text": script.strip()
        }]

    return slides

def attach_words_to_slides(slides: list[dict], words: list[dict]):
    """
    Assign words to slides strictly in sequence.
    Guarantees slide boundaries and correct slide switching.
    """
    word_idx = 0
    total_words = len(words)

    for idx, slide in enumerate(slides):
        slide_word_count = len(slide["text"].split())

        # Safety clamp
        end_idx = min(word_idx + slide_word_count, total_words)

        slide_words = words[word_idx:end_idx]

        if slide_words:
            slide["start"] = slide_words[0]["start"]
            slide["end"] = slide_words[-1]["end"]
        else:
            slide["start"] = 0.0
            slide["end"] = 0.0

        slide["words"] = slide_words
        slide["slide_index"] = idx

        word_idx = end_idx


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
# 1️⃣ SCRIPT + IMAGE GENERATION
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
# 2️⃣ AUDIO + SLIDE SYNC
# --------------------------------------------------

@router.post("/ui/audio", response_class=HTMLResponse)
def generate_audio_ui(
    request: Request,
    script: str = Form(...),
    slides_json: Optional[str] = Form(None)
):
    print("➡️ /ui/audio called")

    if not script or not script.strip():
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Script is empty."}
        )

    if not slides_json:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Slide data missing. Please regenerate the script."}
        )

    try:
        slides = json.loads(slides_json)
    except Exception as e:
        print("❌ slides_json parse failed:", e)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Invalid slide data."}
        )

    try:
        print("🎙️ Generating audio...")
        audio_result = script_to_audio(script)
    except Exception as e:
        print("❌ Audio generation failed:", e)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Audio generation failed."}
        )

    words = audio_result["timestamps"]
    audio_url = audio_result["audio_url"]

    attach_words_to_slides(slides, words)

    return templates.TemplateResponse(
        "player.html",
        {
            "request": request,
            "audio_url": audio_url,
            "slides": slides
        }
    )
