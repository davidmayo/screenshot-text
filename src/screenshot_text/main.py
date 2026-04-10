"""CLI entrypoint for selecting, testing, and watching OCR text."""

from __future__ import annotations

import argparse
from datetime import datetime
import logging
from pathlib import Path
import time

from .actions import handle_accepted_text
from .config import AppConfig, ConfigError, DEFAULT_CONFIG_PATH, RegionConfig, load_config, save_config
from .detector import AcceptedTextEvent, TextDetector
from .ocr import OCRError, ensure_tesseract_available, perform_ocr
from .preprocess import PreprocessError, preprocess_image, save_image
from .region_selector import RegionSelectionError, select_region
from .screen_capture import CaptureError, capture_region


logger = logging.getLogger(__name__)


def main() -> None:
    """Parse CLI args and execute the requested command."""

    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.log_level)

    try:
        exit_code = args.handler(args)
    except (ConfigError, CaptureError, OCRError, PreprocessError, RegionSelectionError) as exc:
        logger.error("%s", exc)
        raise SystemExit(1) from exc
    except KeyboardInterrupt:
        logger.info("Stopped.")
        raise SystemExit(130) from None

    raise SystemExit(exit_code)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to the TOML config file. Default: {DEFAULT_CONFIG_PATH}",
    )

    parser = argparse.ArgumentParser(
        prog="screenshot-text",
        description="Select a screen region, OCR it once, or watch it on a loop.",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging verbosity.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    select_parser = subparsers.add_parser(
        "select",
        parents=[common],
        help="Interactively select and save a screen region.",
    )
    select_parser.set_defaults(handler=handle_select)

    test_parser = subparsers.add_parser(
        "test",
        parents=[common],
        help="Capture the saved region once and print OCR output.",
    )
    test_parser.add_argument(
        "--debug-dir",
        type=Path,
        help="Directory for saving raw and preprocessed images from the test run.",
    )
    test_parser.add_argument(
        "--print-normalized",
        action="store_true",
        help="Also print the normalized OCR text.",
    )
    test_parser.set_defaults(handler=handle_test)

    watch_parser = subparsers.add_parser(
        "watch",
        parents=[common],
        help="Poll the saved region, OCR it, and emit accepted text changes.",
    )
    watch_parser.set_defaults(handler=handle_watch)

    return parser


def handle_select(args: argparse.Namespace) -> int:
    """Select a region and save it into the config file."""

    config_path = args.config.expanduser()
    config = load_config(config_path)
    selected_region = select_region()

    if selected_region is None:
        logger.info("Selection canceled.")
        return 0

    config.region = selected_region
    save_config(config, config_path)

    logger.info(
        "Saved region to %s: x=%d y=%d width=%d height=%d",
        config_path,
        selected_region.x,
        selected_region.y,
        selected_region.width,
        selected_region.height,
    )
    return 0


def handle_test(args: argparse.Namespace) -> int:
    """Run one capture/OCR pass and print the result."""

    config_path = args.config.expanduser()
    config = load_config(config_path)
    region = require_region(config, config_path)
    ensure_tesseract_available()

    raw_image = capture_region(region)
    preprocessed_image = preprocess_image(raw_image, config.preprocess)
    reading = perform_ocr(preprocessed_image, config.ocr)

    debug_dir = resolve_debug_dir(args.debug_dir, config)
    if debug_dir is not None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        save_image(raw_image, debug_dir / f"{timestamp}-raw.png")
        save_image(preprocessed_image, debug_dir / f"{timestamp}-preprocessed.png")
        logger.info("Saved debug images to %s", debug_dir)

    print("Raw OCR text:")
    print(reading.raw_text if reading.raw_text else "<empty>")

    if args.print_normalized:
        print()
        print("Normalized OCR text:")
        print(reading.normalized_text if reading.normalized_text else "<empty>")

    return 0


def handle_watch(args: argparse.Namespace) -> int:
    """Continuously capture and OCR the configured region."""

    config_path = args.config.expanduser()
    config = load_config(config_path)
    region = require_region(config, config_path)
    ensure_tesseract_available()

    detector = TextDetector(require_stable_reads=config.detection.require_stable_reads)
    logger.info(
        "Watching region x=%d y=%d width=%d height=%d every %.2fs",
        region.x,
        region.y,
        region.width,
        region.height,
        config.interval_seconds,
    )

    while True:
        try:
            raw_image = capture_region(region)
            preprocessed_image = preprocess_image(raw_image, config.preprocess)
            reading = perform_ocr(preprocessed_image, config.ocr)
        except (CaptureError, OCRError, PreprocessError) as exc:
            logger.warning("%s", exc)
            time.sleep(config.interval_seconds)
            continue

        event = detector.process(reading)
        if event is not None:
            emit_accepted_text(event)
            handle_accepted_text(event)

        time.sleep(config.interval_seconds)


def require_region(config: AppConfig, config_path: Path) -> RegionConfig:
    """Return the configured region or raise a clear error."""

    if config.region is None:
        raise ConfigError(
            f"No region is configured in {config_path}. Run `screenshot-text select` first."
        )
    return config.region


def resolve_debug_dir(cli_value: Path | None, config: AppConfig) -> Path | None:
    """Choose a debug directory from CLI override or config."""

    if cli_value is not None:
        return cli_value.expanduser()
    return config.debug.save_dir


def emit_accepted_text(event: AcceptedTextEvent) -> None:
    """Print an accepted OCR update in a readable way."""

    timestamp = event.accepted_at.isoformat(timespec="seconds")
    print(f"[{timestamp}] OCR text update:")
    print(event.normalized_text)
    print("--", flush=True)


def configure_logging(level_name: str) -> None:
    """Configure simple stderr logging."""

    logging.basicConfig(
        level=getattr(logging, level_name),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
