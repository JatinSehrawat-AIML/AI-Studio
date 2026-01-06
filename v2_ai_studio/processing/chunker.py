# processing/chunker.py
def chunk_text(text: str, max_words: int = 800, overlap: int = 100):
    """
    Splits text into overlapping word chunks for LLM processing.

    Args:
        text (str): Input text
        max_words (int): Max words per chunk
        overlap (int): Overlapping words between chunks
    """

    if not text or not text.strip():
        raise ValueError("Cannot chunk empty text")

    words = text.split()
    start = 0

    while start < len(words):
        end = start + max_words
        yield " ".join(words[start:end])
        start = end - overlap if end - overlap > 0 else end
