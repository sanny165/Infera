"""
OCR utilities using Tesseract (via pytesseract) for:
  - Standalone images (PNG / JPG / JPEG)
  - Scanned / image-only PDF pages (rendered upstream by pdf_extractor)
"""

from io import BytesIO

import pytesseract
from PIL import Image


class OCRError(Exception):
    pass


def ocr_image(image: Image.Image) -> str:
    """Run Tesseract OCR on a PIL Image and return extracted text."""
    try:
        # Light preprocessing: convert to grayscale for more reliable OCR
        gray = image.convert("L")
        text = pytesseract.image_to_string(gray)
        return text.strip()
    except pytesseract.TesseractNotFoundError as e:
        raise OCRError(
            "Tesseract OCR engine is not installed on this system. "
            "Locally: install Tesseract (see README). "
            "On Streamlit Community Cloud: ensure packages.txt contains 'tesseract-ocr'."
        ) from e
    except Exception as e:
        raise OCRError(f"OCR failed: {e}") from e


def ocr_image_bytes(file_bytes: bytes) -> str:
    """Convenience wrapper: OCR an uploaded image file's raw bytes."""
    image = Image.open(BytesIO(file_bytes))
    return ocr_image(image)
