import os
from dotenv import load_dotenv
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router as api_router
from app.ui_routes import router as ui_router
from utils.cleanup import cleanup_directories

# --------------------------------------------------
# 🌍 ENV LOADING (DEPLOYMENT SAFE)
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]  # project root
ENV_FILE = BASE_DIR / ".env"

# Load .env only if present (local dev)
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Log (do NOT crash here)
print("GROQ_API_KEY loaded:", bool(os.getenv("GROQ_API_KEY")))

# --------------------------------------------------
# 🔁 LIFESPAN
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 AI Tutor Studio starting...")
    yield
    print("🧹 Server shutting down — cleaning generated files")

    cleanup_directories(
        dirs=[
            BASE_DIR / "static/generated/scenes",
            BASE_DIR / "static/audio_meta",
            BASE_DIR / "uploads",
            BASE_DIR / "static/frames",
            BASE_DIR / "static/videos",
            BASE_DIR / "static/audio",
        ],
        keep_latest=False
    )

# --------------------------------------------------
# FASTAPI APP
# --------------------------------------------------

app = FastAPI(
    title="AI Tutor Studio",
    description="Generate YouTube-style tutorial scripts from PDFs and PPTs",
    version="1.0.0",
    lifespan=lifespan
)

# --------------------------------------------------
# STATIC FILES
# --------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

app.include_router(ui_router)
app.include_router(api_router)