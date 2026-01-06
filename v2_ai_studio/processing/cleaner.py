# processing/cleaner.py
import re


def clean_text(text: str) -> str:
    """
    Cleans extracted text by removing excessive whitespace
    and common document artifacts while preserving meaning.
    """

    if not text or not text.strip():
        raise ValueError("Empty text cannot be cleaned")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove common PDF artifacts
    text = re.sub(r"\b(Page|page)\s+\d+\b", "", text)

    # Remove repeated separators
    text = re.sub(r"[_\-]{2,}", " ", text)

    return text.strip()
