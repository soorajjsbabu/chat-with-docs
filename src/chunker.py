"""Text chunker for the RAG application.

Splits long documents into smaller overlapping chunks so they can be
embedded and retrieved individually. Overlap preserves context across
chunk boundaries, improving retrieval quality in a RAG system.
"""

from typing import List


def split_text(text: str, size: int, overlap: int) -> List[str]:
    """Split a string into overlapping chunks using a sliding window.

    Args:
        text: The full document text to split.
        size: Maximum number of characters per chunk.
        overlap: Number of characters that overlap between consecutive chunks.
                 This keeps context intact so ideas that cross a boundary
                 aren't split in half, which improves retrieval accuracy.

    Returns:
        A list of text chunks.
    """
    # Overlap must be less than chunk size, otherwise we would make
    # no forward progress and could loop forever.
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    # If the text is already small enough, return it as a single chunk.
    if len(text) <= size:
        return [text]

    chunks: List[str] = []
    start = 0

    # Slide the window forward by (size - overlap) each iteration.
    # This means the end of one chunk repeats at the start of the next,
    # which is why overlap matters in RAG:
    #
    # 1. Context preservation — sentences or ideas that cross a boundary
    #    appear in both chunks, so neither chunk loses meaning.
    #
    # 2. Better retrieval — a query about a concept near a boundary is
    #    more likely to match a chunk that still contains the full idea.
    #
    # 3. Smoother answers — the LLM receives surrounding context for each
    #    chunk, reducing disjointed or incomplete responses.
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        chunks.append(chunk)

        # Advance the window, keeping 'overlap' characters from the
        # previous chunk so context carries over.
        start += size - overlap

    return chunks
