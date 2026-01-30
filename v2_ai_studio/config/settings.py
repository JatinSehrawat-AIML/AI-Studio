from pathlib import Path
import os
from dotenv import load_dotenv

# --------------------------------------------------
# ENV LOADING
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

# --------------------------------------------------
# HUGGING FACE CONFIG
# --------------------------------------------------

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# Default model (can be overridden via .env)
HF_MODEL = os.getenv(
    "HF_MODEL",
    "mistralai/zephyr-7b-beta"
)

# --------------------------------------------------
# PROCESSING DEFAULTS
# --------------------------------------------------

MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))

# --------------------------------------------------
# SAFETY CHECKS
# --------------------------------------------------

if not HF_API_TOKEN:
    raise RuntimeError(
        "HF_API_TOKEN is not set in config/.env file"
    )
