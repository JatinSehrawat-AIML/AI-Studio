import pdfplumber
from pathlib import Path


def load_pdf(path: str) -> str:
    pdf_path = Path(path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"

    if not text.strip():
        raise ValueError("No readable text found in PDF")

    return text
