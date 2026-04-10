from __future__ import annotations

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from screenshot_text.detector import TextDetector  # noqa: E402
from screenshot_text.ocr import OCRText  # noqa: E402


class TextDetectorTests(unittest.TestCase):
    def test_accepts_new_text_immediately_when_stability_is_one(self) -> None:
        detector = TextDetector(require_stable_reads=1)

        event = detector.process(OCRText(raw_text="hello", normalized_text="hello"))

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.normalized_text, "hello")
        self.assertEqual(event.raw_text, "hello")

    def test_ignores_duplicate_text_after_acceptance(self) -> None:
        detector = TextDetector(require_stable_reads=1)

        first = detector.process(OCRText(raw_text="same", normalized_text="same"))
        second = detector.process(OCRText(raw_text="same", normalized_text="same"))

        self.assertIsNotNone(first)
        self.assertIsNone(second)

    def test_ignores_empty_text(self) -> None:
        detector = TextDetector(require_stable_reads=1)

        event = detector.process(OCRText(raw_text="   ", normalized_text=""))

        self.assertIsNone(event)

    def test_requires_two_matching_reads_when_configured(self) -> None:
        detector = TextDetector(require_stable_reads=2)

        first = detector.process(OCRText(raw_text="alpha", normalized_text="alpha"))
        second = detector.process(OCRText(raw_text="alpha", normalized_text="alpha"))

        self.assertIsNone(first)
        self.assertIsNotNone(second)
        assert second is not None
        self.assertEqual(second.normalized_text, "alpha")
