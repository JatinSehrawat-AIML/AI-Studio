from loaders.pdf_loader import load_pdf
from loaders.ppt_loader import load_ppt
from processing.cleaner import clean_text
from processing.chunker import chunk_text
from llm.script_generator import generate_slidewise_script


def generate_script_from_file(
    file_path: str,
    tone: str = "educational"
) -> str:
    # 1️⃣ Load document
    if file_path.lower().endswith(".pdf"):
        raw_text = load_pdf(file_path)
    elif file_path.lower().endswith(".pptx"):
        raw_text = load_ppt(file_path)
    else:
        raise ValueError("Unsupported file format")

    if not raw_text.strip():
        raise ValueError("No readable text found in file")

    # 2️⃣ Clean + chunk
    cleaned_text = clean_text(raw_text)
    chunks = list(chunk_text(cleaned_text))

    if not chunks:
        raise ValueError("No meaningful content after processing")

    # 3️⃣ Convert chunks → slide-wise structure
    slides = [
        {
            "slide": idx + 1,
            "content": chunk
        }
        for idx, chunk in enumerate(chunks, start=1)
    ]

    return generate_slidewise_script(slides, tone=tone)