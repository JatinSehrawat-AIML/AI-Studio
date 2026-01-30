from fastapi import APIRouter, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

import os
import uuid
import re
import json
import logging

from services.script_service import generate_script_from_file
from llm.diagram_planner import generate_architecture_plan
from diagram.frame_generator import progressive_frames, render_frame
from tts.audio_generator import script_to_audio
from video.moviepy_builder import build_video_from_frames
from utils.cleanup import cleanup_directories

# 🔥 KEY IMPORTS (keyword-driven diagrams)
from diagram.keyword_extractor import extract_keywords_from_slide
from diagram.keyword_to_graph import keywords_to_graph

# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# ROUTER SETUP
# --------------------------------------------------

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
FRAME_DIR = "static/frames"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRAME_DIR, exist_ok=True)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def parse_slides_from_script(script: str) -> list[dict]:
    slides = []
    pattern = re.compile(r"(Slide\s+\d+\s*:)", re.IGNORECASE)
    parts = pattern.split(script)

    if len(parts) == 1:
        return [{
            "title": "Slide 1:",
            "text": script.strip(),
            "slide_index": 0
        }]

    idx = 0
    for i in range(1, len(parts), 2):
        slides.append({
            "title": parts[i].strip(),
            "text": parts[i + 1].strip() if i + 1 < len(parts) else "",
            "slide_index": idx
        })
        idx += 1

    return slides


def normalize_slides(slides: list[dict]) -> list[dict]:
    return [{
        "title": s.get("title", f"Slide {i+1}:"),
        "text": s.get("text", ""),
        "frames": [],
        "words": [],
        "start": 0.0,
        "end": 0.0,
        "slide_index": s.get("slide_index", i)
    } for i, s in enumerate(slides)]


def attach_words_to_slides(slides: list[dict], words: list[dict]):
    word_idx = 0
    for slide in slides:
        wc = len(slide["text"].split())
        slide_words = words[word_idx: word_idx + wc]

        if slide_words:
            slide["start"] = slide_words[0]["start"]
            slide["end"] = slide_words[-1]["end"]

        slide["words"] = slide_words
        word_idx += wc

    if slides and words:
        slides[-1]["end"] = words[-1]["end"]

# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


SLIDE_COMPLEXITY = {
    0: 2,
    1: 4,
    2: 5,
    3: 6,
}

# --------------------------------------------------
# SCRIPT + DIAGRAM GENERATION
# --------------------------------------------------

@router.post("/ui/generate", response_class=HTMLResponse)
async def generate_script_ui(
    request: Request,
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith((".pdf", ".pptx")):
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Only PDF and PPTX files are supported."}
        )

    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        # 1️⃣ Generate narration script (for audio ONLY)
        script = generate_script_from_file(file_path)
        if not script.strip():
            raise RuntimeError("Generated script is empty")

        # 2️⃣ Slides (used for BOTH script + diagrams)
        slides = normalize_slides(parse_slides_from_script(script))

        # 3️⃣ Cleanup old frames
        cleanup_directories([FRAME_DIR], keep_latest=False)
        global_frame_counter = 1

        # 4️⃣ Generate diagrams PER SLIDE (KEYWORD-DRIVEN)
        for slide in slides:
            slide_index = slide["slide_index"]
            slide_text = slide["text"]

            # 🔑 A) Extract keywords/components from slide text
            keyword_data = extract_keywords_from_slide(slide_text)

            # 🔑 B) Convert keywords → architecture graph
            keyword_graph = keywords_to_graph(keyword_data)

            # 🔁 C) Fallback ONLY if keyword extraction fails
            if not keyword_graph.get("nodes"):
                logger.warning(
                    "Keyword graph empty, falling back to architecture planner"
                )
                keyword_graph = generate_architecture_plan(
                    slide_text,
                    max_nodes=SLIDE_COMPLEXITY.get(slide_index, 6),
                    slide_index=slide_index
                )

            # 🔑 D) Generate progressive frames
            slide_frames = progressive_frames(
                keyword_graph,
                mode="architecture"
            )

            slide["frames"] = []

            for frame_plan in slide_frames:
                try:
                    frame_path = render_frame(frame_plan, global_frame_counter)
                    if frame_path:
                        slide["frames"].append(
                            "/" + frame_path.replace("\\", "/")
                        )
                        global_frame_counter += 1
                except Exception as e:
                    logger.error(f"Frame render failed: {e}")

    except Exception as e:
        logger.exception("Script / diagram generation failed")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(e)}
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "script": script,
            "slides": slides,
            "slides_json": json.dumps(slides)
        }
    )

# --------------------------------------------------
# AUDIO + VIDEO
# --------------------------------------------------

@router.post("/ui/audio", response_class=HTMLResponse)
def generate_audio_ui(
    request: Request,
    background_tasks: BackgroundTasks,
    script: str = Form(...),
    slides_json: Optional[str] = Form(None)
):
    slides = json.loads(slides_json)

    audio_result = script_to_audio(script)
    audio_url = audio_result["audio_url"]
    words = audio_result["timestamps"]

    attach_words_to_slides(slides, words)

    background_tasks.add_task(
        build_video_from_frames,
        slides=slides,
        audio_path=audio_url.lstrip("/")
    )

    return templates.TemplateResponse(
        "player.html",
        {
            "request": request,
            "audio_url": audio_url,
            "slides": slides,
            "video_url": "/static/videos/final_demo.mp4"
        }
    )
