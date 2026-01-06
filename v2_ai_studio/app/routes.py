from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse

from services.script_service import generate_script_from_file
from tts.audio_generator import script_to_audio

import os
import uuid

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------- HEALTH ----------------
@router.get("/health")
def health_check():
    return {"status": "ok"}


# ---------------- SCRIPT GENERATION ----------------
@router.post("/generate-script")
async def generate_script_api(
    file: UploadFile = File(..., description="Upload a PDF or PPTX file"),
    tone: str = "educational"
):
    filename = file.filename.lower()

    if not filename.endswith((".pdf", ".pptx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and PPTX files are supported"
        )

    file_id = str(uuid.uuid4())
    saved_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    with open(saved_path, "wb") as f:
        f.write(await file.read())

    try:
        script = generate_script_from_file(saved_path)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "tone": tone,
                "script": script
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(saved_path):
            os.remove(saved_path)


# ---------------- AUDIO GENERATION ----------------
@router.post("/generate-audio")
async def generate_audio_api(script: str):
    """
    Converts narration script to audio.
    Returns the audio file directly.
    """
    if not script.strip():
        raise HTTPException(
            status_code=400,
            detail="Script text cannot be empty"
        )

    audio_result = script_to_audio(script)

    return FileResponse(
        audio_result["audio_url"],
        media_type="audio/mpeg",
        filename="tutorial_audio.mp3"
    )
