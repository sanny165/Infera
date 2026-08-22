"""
Text cleaning, normalization, and page-aware chunking.

Produces a flat list of chunk dicts:
    {"chunk_id": int, "page": int, "text": str}

Keeping the source page on every chunk lets the RAG layer cite
"This information was found on page X" for grounded answers.
"""

import re
from typing import List, TypedDict

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE


class Chunk(TypedDict):
    chunk_id: int
    page: int
    text: str


def clean_text(text: str) -> str:
    """Remove excessive whitespace / normalize a block of extracted text."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ blank lines into a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse runs of spaces/tabs
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Strip trailing whitespace per line
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text.strip()


def chunk_pages(pages: List[dict]) -> List[Chunk]:
    """
    pages: list of {"page": int, "text": str} (already cleaned)
    Splits each page's text into overlapping chunks while preserving page number.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: List[Chunk] = []
    chunk_id = 0
    for page in pages:
        page_text = page["text"]
        if not page_text:
            continue
        for piece in splitter.split_text(page_text):
            piece = piece.strip()
            if not piece:
                continue
            chunks.append({"chunk_id": chunk_id, "page": page["page"], "text": piece})
            chunk_id += 1
    return chunks


def build_full_text(pages: List[dict]) -> str:
    """Concatenate all cleaned page text into one document string (for summarization)."""
    parts = []
    for page in pages:
        if page["text"]:
            parts.append(f"[Page {page['page']}]\n{page['text']}")
    return "\n\n".join(parts)
