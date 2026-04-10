"""Stateful OCR change detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .ocr import OCRText


@dataclass(slots=True)
class AcceptedTextEvent:
    """Accepted OCR text ready to print and pass to the action hook."""

    raw_text: str
    normalized_text: str
    accepted_at: datetime


class TextDetector:
    """Accept OCR text only when it is new and sufficiently stable."""

    def __init__(self, require_stable_reads: int = 1) -> None:
        if require_stable_reads <= 0:
            raise ValueError("require_stable_reads must be greater than zero.")

        self.require_stable_reads = require_stable_reads
        self._last_accepted_text: str | None = None
        self._candidate_text: str | None = None
        self._candidate_count = 0

    def process(self, reading: OCRText) -> AcceptedTextEvent | None:
        """Return an accepted event when the text is worth acting on."""

        text = reading.normalized_text
        if not text:
            self._candidate_text = None
            self._candidate_count = 0
            return None

        if text == self._last_accepted_text:
            return None

        if self.require_stable_reads == 1:
            return self._accept(reading)

        if text == self._candidate_text:
            self._candidate_count += 1
        else:
            self._candidate_text = text
            self._candidate_count = 1

        if self._candidate_count >= self.require_stable_reads:
            return self._accept(reading)

        return None

    def _accept(self, reading: OCRText) -> AcceptedTextEvent:
        self._last_accepted_text = reading.normalized_text
        self._candidate_text = None
        self._candidate_count = 0
        return AcceptedTextEvent(
            raw_text=reading.raw_text,
            normalized_text=reading.normalized_text,
            accepted_at=datetime.now(),
        )
