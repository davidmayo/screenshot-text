"""Capture a selected screen region."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .config import RegionConfig

if TYPE_CHECKING:
    from PIL.Image import Image


class CaptureError(RuntimeError):
    """Raised when screenshot capture cannot be completed."""


def capture_region(region: RegionConfig) -> "Image":
    """Capture a PIL image for the requested screen region."""

    try:
        from mss import mss
    except ModuleNotFoundError as exc:
        raise CaptureError("Missing Python dependency `mss`. Run `uv sync` to install it.") from exc

    try:
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise CaptureError("Missing Python dependency `Pillow`. Run `uv sync` to install it.") from exc

    monitor = {
        "top": region.y,
        "left": region.x,
        "width": region.width,
        "height": region.height,
    }

    try:
        with mss() as screenshotter:
            shot = screenshotter.grab(monitor)
    except Exception as exc:  # pragma: no cover - depends on live desktop access.
        raise CaptureError(f"Failed to capture screen region {monitor}: {exc}") from exc

    return Image.frombytes("RGB", shot.size, shot.rgb)
