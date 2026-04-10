"""Tesseract OCR wrapper and conservative text normalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import OcrConfig

if TYPE_CHECKING:
    from PIL.Image import Image


class OCRError(RuntimeError):
    """Raised when OCR dependencies or Tesseract are unavailable."""


@dataclass(slots=True)
class OCRText:
    """Raw and normalized OCR text for a single capture."""

    raw_text: str
    normalized_text: str


def ensure_tesseract_available() -> None:
    """Fail fast with a helpful message when Tesseract is unavailable."""

    pytesseract = _load_pytesseract()

    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRError(
            "Tesseract is not installed or not on PATH. Install `tesseract-ocr` and try again."
        ) from exc


def perform_ocr(image: "Image", settings: OcrConfig) -> OCRText:
    """Run Tesseract and return both raw and normalized text."""

    pytesseract = _load_pytesseract()
    config = f"--psm {settings.psm}"

    try:
        raw_text = pytesseract.image_to_string(image, lang=settings.lang, config=config)
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRError(
            "Tesseract is not installed or not on PATH. Install `tesseract-ocr` and try again."
        ) from exc
    except pytesseract.TesseractError as exc:
        raise OCRError(f"Tesseract OCR failed: {exc}") from exc

    return OCRText(raw_text=raw_text, normalized_text=normalize_text(raw_text))


def normalize_text(text: str) -> str:
    """Normalize OCR text conservatively for change detection."""

    normalized = text.replace("\x0c", "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized_lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(normalized_lines).strip()


def _load_pytesseract():
    try:
        import pytesseract
    except ModuleNotFoundError as exc:
        raise OCRError("Missing Python dependency `pytesseract`. Run `uv sync` to install it.") from exc

    return pytesseract
