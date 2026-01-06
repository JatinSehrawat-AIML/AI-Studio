from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routes import router as api_router
from app.ui_routes import router as ui_router
from utils.cleanup import cleanup_directories


BASE_DIR = Path(__file__).resolve().parents[1]  # ai_studio/

app = FastAPI(
    title="AI Tutor Studio",
    description="Generate YouTube-style tutorial scripts from PDFs and PPTs",
    version="1.0.0"
)

@app.on_event("shutdown")
def cleanup_on_shutdown():
    print("🧹 Server shutting down — cleaning generated files")

    cleanup_directories([
        "static/generated/scenes",
        "static/audio",
        "static/audio_meta",
        "uploads"
    ])

# ✅ THIS IS THE KEY FIX
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

app.include_router(ui_router)
app.include_router(api_router)
