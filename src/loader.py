"""Document loader for the RAG application.

This module provides functions to load documents from a directory.
It supports PDF files (via pypdf) and plain-text files (.txt, .md).
Each loaded document is returned as a dictionary containing the
filename and the full text content. Empty files are skipped.
"""

from io import BytesIO
from pathlib import Path
from typing import List, Dict, Optional


def _load_pdf(path: Path) -> str:
    """Extract text from a PDF file using pypdf.

    Args:
        path: Path to the PDF file.

    Returns:
        The extracted text joined from all pages.
    """
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)


def _load_text(path: Path) -> str:
    """Read the contents of a plain-text file.

    Args:
        path: Path to the text file.

    Returns:
        The file contents as a string.
    """
    return path.read_text(encoding="utf-8")


def _load_pdf_from_bytes(content: bytes) -> str:
    """Extract text from PDF bytes."""
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(content))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)


def load_document_from_bytes(content: bytes, filename: str) -> Optional[Dict[str, str]]:
    """Load a single document from raw bytes.

    Args:
        content: The raw file bytes.
        filename: The original filename (used to determine file type).

    Returns:
        A dict with 'source' and 'text', or None if unsupported or empty.
    """
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        text = _load_pdf_from_bytes(content)
    elif suffix in (".txt", ".md"):
        text = content.decode("utf-8")
    else:
        return None

    if not text.strip():
        return None

    return {"source": filename, "text": text}


def load_documents(folder: Path) -> List[Dict[str, str]]:
    """Load all supported documents from a folder.

    Iterates over the directory, reads each supported file (.pdf, .txt, .md),
    and collects them into a list of dictionaries. Files with no extractable
    text are skipped.

    Args:
        folder: The directory to scan for documents.

    Returns:
        A list of dicts, each with keys 'source' (filename) and 'text' (content).
    """
    documents: List[Dict[str, str]] = []

    # Only process files that exist and are supported
    for file_path in folder.iterdir():
        if not file_path.is_file():
            continue

        # Choose the appropriate loader based on file extension
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            text = _load_pdf(file_path)
        elif suffix in (".txt", ".md"):
            text = _load_text(file_path)
        else:
            # Skip unsupported file types
            continue

        # Skip files that yielded no text
        if not text.strip():
            continue

        documents.append({"source": file_path.name, "text": text})

    return documents
