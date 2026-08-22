
# """
# OCR utilities using Tesseract (via pytesseract) for:
#   - Standalone images (PNG / JPG / JPEG)
#   - Scanned / image-only PDF pages (rendered upstream by pdf_extractor)

# Supports multilingual OCR across English, Telugu, Hindi, Tamil, and Bengali.
# """

# from io import BytesIO
# from typing import List, Union

# import pytesseract
# from PIL import Image

# # Language codes supported by Tesseract
# SUPPORTED_LANGUAGES = {
#     "eng": "English",
#     "tel": "Telugu",
#     "hin": "Hindi",
#     "tam": "Tamil",
#     "ben": "Bengali",
# }

# DEFAULT_LANGUAGES = "eng+tel+hin+tam+ben"


# class OCRError(Exception):
#     pass


# def format_language_string(lang: Union[str, List[str]]) -> str:
#     """Helper to convert a list of language codes or a string into Tesseract syntax."""
#     if isinstance(lang, list):
#         return "+".join(lang)
#     return lang


# def ocr_image(image: Image.Image, lang: Union[str, List[str]] = DEFAULT_LANGUAGES) -> str:
#     """Run Tesseract OCR on a PIL Image and return extracted text.

#     :param image: PIL Image instance.
#     :param lang: Tesseract language code string (e.g. 'eng+hin') or list (e.g. ['eng', 'hin']).
#                  Defaults to 'eng+tel+hin+tam+ben'.
#     """
#     lang_str = format_language_string(lang)
    
#     try:
#         # Grayscale conversion improves OCR accuracy on document scans
#         gray = image.convert("L")
#         text = pytesseract.image_to_string(gray, lang=lang_str)
#         return text.strip()

#     except pytesseract.TesseractNotFoundError as e:
#         raise OCRError(
#             "Tesseract OCR engine is not installed on this system.\n"
#             "- Locally: Install Tesseract and language packages (see README).\n"
#             "- Streamlit Cloud: Include 'tesseract-ocr' and specific language packages "
#             "(e.g., tesseract-ocr-tel, tesseract-ocr-hin, tesseract-ocr-tam, tesseract-ocr-ben) "
#             "in packages.txt."
#         ) from e

#     except pytesseract.TesseractError as e:
#         err_msg = str(e)
#         if "Invalid language code" in err_msg or "failed loading language" in err_msg:
#             raise OCRError(
#                 f"Tesseract language data for configuration '{lang_str}' is incomplete or missing.\n"
#                 "Ensure the required traineddata files (eng, tel, hin, tam, ben) are present in your tessdata folder "
#                 "or installed via system package manager."
#             ) from e
#         raise OCRError(f"OCR execution failed: {e}") from e

#     except Exception as e:
#         raise OCRError(f"OCR failed due to an unexpected error: {e}") from e


# def ocr_image_bytes(file_bytes: bytes, lang: Union[str, List[str]] = DEFAULT_LANGUAGES) -> str:
#     """Convenience wrapper: OCR an uploaded image file's raw bytes."""
#     try:
#         image = Image.open(BytesIO(file_bytes))
#         return ocr_image(image, lang=lang)
#     except Exception as e:
#         if isinstance(e, OCRError):
#             raise e
#         raise OCRError(f"Failed to load image from bytes: {e}") from e


"""
OCR utilities using Tesseract (via pytesseract) for:
  - Standalone images (PNG / JPG / JPEG)
  - Scanned / image-only PDF pages (rendered upstream by pdf_extractor)

Supports targeted OCR for English, Telugu, Hindi, Tamil, and Bengali to prevent script confusion.
"""

from io import BytesIO
from typing import List, Union

import pytesseract
from PIL import Image

# Language codes supported by Tesseract
SUPPORTED_LANGUAGES = {
    "eng": "English",
    "hin": "Hindi",
    "tel": "Telugu",
    "tam": "Tamil",
    "ben": "Bengali",
    "hin+eng": "Hindi + English",
    "tel+eng": "Telugu + English",
    "tam+eng": "Tamil + English",
    "ben+eng": "Bengali + English",
}

DEFAULT_LANGUAGE = "hin+eng"


class OCRError(Exception):
    pass


def format_language_string(lang: Union[str, List[str]]) -> str:
    """Helper to convert a list of language codes or a string into Tesseract syntax."""
    if isinstance(lang, list):
        return "+".join(lang)
    return lang


def ocr_image(image: Image.Image, lang: Union[str, List[str]] = DEFAULT_LANGUAGE) -> str:
    """Run Tesseract OCR on a PIL Image and return extracted text.

    :param image: PIL Image instance.
    :param lang: Tesseract language code string (e.g., 'hin', 'hin+eng') or list (e.g., ['hin', 'eng']).
                 Defaults to 'hin+eng'.
    """
    lang_str = format_language_string(lang)
    
    try:
        # Light preprocessing: convert to grayscale for more reliable OCR
        gray = image.convert("L")
        text = pytesseract.image_to_string(gray, lang=lang_str)
        return text.strip()

    except pytesseract.TesseractNotFoundError as e:
        raise OCRError(
            "Tesseract OCR engine is not installed on this system.\n"
            "- Locally: Install Tesseract and language packages (see README).\n"
            "- Streamlit Cloud: Include 'tesseract-ocr' and specific language packages "
            "(e.g., tesseract-ocr-hin, tesseract-ocr-tel, tesseract-ocr-tam, tesseract-ocr-ben) "
            "in packages.txt."
        ) from e

    except pytesseract.TesseractError as e:
        err_msg = str(e)
        if "Invalid language code" in err_msg or "failed loading language" in err_msg:
            raise OCRError(
                f"Tesseract language data for '{lang_str}' is incomplete or missing.\n"
                "Ensure the required traineddata file is present in your tessdata folder "
                "or installed via system package manager."
            ) from e
        raise OCRError(f"OCR execution failed: {e}") from e

    except Exception as e:
        raise OCRError(f"OCR failed due to an unexpected error: {e}") from e


def ocr_image_bytes(file_bytes: bytes, lang: Union[str, List[str]] = DEFAULT_LANGUAGE) -> str:
    """Convenience wrapper: OCR an uploaded image file's raw bytes."""
    try:
        image = Image.open(BytesIO(file_bytes))
        return ocr_image(image, lang=lang)
    except Exception as e:
        if isinstance(e, OCRError):
            raise e
        raise OCRError(f"Failed to load image from bytes: {e}") from e
