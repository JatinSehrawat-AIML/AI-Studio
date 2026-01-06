from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model config (future-proof)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

# Processing defaults
MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in config/.env file")

