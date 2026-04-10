from __future__ import annotations

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from screenshot_text.ocr import normalize_text  # noqa: E402


class NormalizeTextTests(unittest.TestCase):
    def test_normalize_text_trims_trailing_space_and_normalizes_line_endings(self) -> None:
        raw_text = "  hello  \r\nworld\t \r\nline three\x0c"

        normalized = normalize_text(raw_text)

        self.assertEqual(normalized, "hello\nworld\nline three")

    def test_normalize_text_returns_empty_for_whitespace_only_input(self) -> None:
        self.assertEqual(normalize_text(" \r\n\t "), "")
