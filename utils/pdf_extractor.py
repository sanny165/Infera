"""
PDF text extraction using PyMuPDF (fitz).

Handles both:
  - Normal (digitally generated) PDFs -> direct text extraction
  - Scanned PDFs -> pages are rendered to images for the OCR module to read

Keeps per-page structure so downstream chunking can preserve page metadata.
"""

from dataclasses import dataclass
from typing import List

import fitz  # PyMuPDF
from PIL import Image

from config import MIN_CHARS_PER_PAGE_FOR_TEXT_PDF


@dataclass
class PageContent:
    page_number: int  # 1-indexed, for user-facing citations
    text: str
    needs_ocr: bool = False


def open_pdf(file_bytes: bytes) -> fitz.Document:
    return fitz.open(stream=file_bytes, filetype="pdf")


def extract_text_per_page(doc: fitz.Document) -> List[PageContent]:
    """Direct text-layer extraction. Marks pages with little/no text as needing OCR."""
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        pages.append(
            PageContent(
                page_number=i + 1,
                text=text.strip(),
                needs_ocr=len(text.strip()) < MIN_CHARS_PER_PAGE_FOR_TEXT_PDF,
            )
        )
    return pages


def render_page_as_image(doc: fitz.Document, page_index: int, zoom: float = 2.0) -> Image.Image:
    """Render a PDF page to a PIL Image (used when the page has no text layer)."""
    page = doc[page_index]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def document_is_mostly_scanned(pages: List[PageContent]) -> bool:
    """True if the vast majority of pages have no usable text layer."""
    if not pages:
        return True
    ocr_pages = sum(1 for p in pages if p.needs_ocr)
    return ocr_pages / len(pages) > 0.5
