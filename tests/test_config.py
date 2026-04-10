from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from screenshot_text.config import (  # noqa: E402
    AppConfig,
    DebugConfig,
    DetectionConfig,
    OcrConfig,
    PreprocessConfig,
    RegionConfig,
    load_config,
    save_config,
)


class ConfigTests(unittest.TestCase):
    def test_missing_config_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_config(Path(temp_dir) / "missing.toml")

        self.assertEqual(config.interval_seconds, 2.0)
        self.assertIsNone(config.region)
        self.assertEqual(config.ocr.lang, "eng")
        self.assertEqual(config.ocr.psm, 6)
        self.assertEqual(config.preprocess.upscale, 2)
        self.assertEqual(config.detection.require_stable_reads, 1)

    def test_save_and_reload_preserves_existing_settings_when_region_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_path = temp_path / "config.toml"

            original = AppConfig(
                interval_seconds=1.5,
                region=RegionConfig(x=1, y=2, width=300, height=150),
                ocr=OcrConfig(lang="eng", psm=7),
                preprocess=PreprocessConfig(
                    grayscale=True,
                    upscale=3,
                    threshold=190,
                    invert=True,
                ),
                detection=DetectionConfig(require_stable_reads=2),
                debug=DebugConfig(save_dir=temp_path / "debug"),
            )
            save_config(original, config_path)

            updated = load_config(config_path)
            updated.region = RegionConfig(x=10, y=20, width=640, height=320)
            save_config(updated, config_path)

            reloaded = load_config(config_path)

        self.assertIsNotNone(reloaded.region)
        self.assertEqual(reloaded.region.x, 10)
        self.assertEqual(reloaded.region.y, 20)
        self.assertEqual(reloaded.region.width, 640)
        self.assertEqual(reloaded.region.height, 320)
        self.assertEqual(reloaded.interval_seconds, 1.5)
        self.assertEqual(reloaded.ocr.psm, 7)
        self.assertTrue(reloaded.preprocess.invert)
        self.assertEqual(reloaded.preprocess.threshold, 190)
        self.assertEqual(reloaded.detection.require_stable_reads, 2)
        self.assertEqual(reloaded.debug.save_dir, temp_path / "debug")
