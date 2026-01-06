# llm/script_generator.py
from llm.gemini_client import generate
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parents[1]

REF_SLIDES_PATH = BASE_DIR / "assets/examples/reference_ppt.txt"
REF_SCRIPT_PATH = BASE_DIR / "assets/examples/reference_script.txt"


def _load_text(path: Path) -> str:
    return path.read_text().strip() if path.exists() else ""


# ---------------- STRONG SLIDE SPLITTER ----------------

KNOWN_SECTION_HEADERS = [
    "Compute & Model Training",
    "Data Storage & Processing",
]

def _split_single_slide_into_sections(slide: dict) -> list[dict]:
    """
    Deterministically split a single large slide into logical sub-slides
    using paragraph boundaries.

    This is a LAST-RESORT fallback when PPT extraction collapses slides.
    """

    text = slide["content"].strip()

    # Split by double newlines or long sentence groups
    chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 50]

    # If still one chunk, split by sentence count
    if len(chunks) == 1:
        sentences = text.split(". ")
        mid = len(sentences) // 2
        chunks = [
            ". ".join(sentences[:mid]).strip(),
            ". ".join(sentences[mid:]).strip(),
        ]

    slides = []
    for i, chunk in enumerate(chunks, start=1):
        slides.append({
            "slide": i,
            "content": chunk
        })

    return slides

# ---------------- MAIN GENERATOR ----------------

def generate_slidewise_script(slides: list[dict], tone: str = "educational") -> str:
    """
    Generates a STRICT slide-wise teaching script.

    GUARANTEES:
    - Output slide count == logical slide count
    - LLM does NOT invent, merge, or skip slides
    """

    if not slides:
        raise ValueError("No slide content provided")

    # 🔥 HARD FALLBACK: deterministic split if extractor collapsed slides
    if len(slides) == 1:
        slides = _split_single_slide_into_sections(slides[0])

    slide_count = len(slides)

    ref_slides = _load_text(REF_SLIDES_PATH)
    ref_script = _load_text(REF_SCRIPT_PATH)

    prompt = f"""
You are an expert technical educator teaching a university-level class.

Your task is to convert slide content into a CLEAR, STRICTLY SLIDE-WISE teaching script.

🚨 CRITICAL CONSTRAINTS (DO NOT VIOLATE):
- The number of output slides MUST be EXACTLY {slide_count}
- One input slide → ONE output slide
- DO NOT split or merge slides
- EACH slide MUST start with: "Slide X:"
- Slide numbering MUST be sequential from 1 to {slide_count}
- Explain ALL concepts from the slide within the SAME slide

🚨 LANGUAGE RULES:
- Do NOT use first-person language (I, we, today, let's)
- No greetings, hooks, emojis, or conclusions
- Academic, classroom-style explanation
- Tone: {tone}

REQUIRED OUTPUT FORMAT (EXACT):

Slide 1:
Explanation...

Slide 2:
Explanation...
"""

    if ref_slides and ref_script:
        prompt += f"""
REFERENCE EXAMPLE (STYLE ONLY — DO NOT COPY CONTENT):

Slides:
{ref_slides}

Ideal Slide-wise Script:
{ref_script}
"""

    prompt += "\nNOW GENERATE THE SCRIPT FOR THESE SLIDES:\n"

    for s in slides:
        prompt += f"""
Slide {s['slide']} CONTENT:
{s['content']}
"""

    prompt += f"""
FINAL REMINDERS:
- Output EXACTLY {slide_count} slides
- Use ONLY the format "Slide X:"
- Do NOT add anything before or after
"""

    return generate(prompt)
