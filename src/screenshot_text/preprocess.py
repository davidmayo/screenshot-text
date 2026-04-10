"""OCR-oriented image preprocessing helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .config import PreprocessConfig

if TYPE_CHECKING:
    from PIL.Image import Image


class PreprocessError(RuntimeError):
    """Raised when image preprocessing cannot be completed."""


def preprocess_image(image: "Image", settings: PreprocessConfig) -> "Image":
    """Apply a simple preprocessing pipeline that is easy to tune and inspect."""

    try:
        from PIL import ImageOps
    except ModuleNotFoundError as exc:
        raise PreprocessError("Missing Python dependency `Pillow`. Run `uv sync` to install it.") from exc

    working = image

    if settings.upscale > 1:
        resample_module = _load_pillow_image_module()
        working = working.resize(
            (working.width * settings.upscale, working.height * settings.upscale),
            resample_module.Resampling.LANCZOS,
        )

    if settings.grayscale or settings.invert or settings.threshold is not None:
        working = ImageOps.grayscale(working)

    if settings.threshold is not None:
        working = working.point(
            lambda value: 255 if value >= settings.threshold else 0,
            mode="L",
        )

    if settings.invert:
        working = ImageOps.invert(working)

    return working


def save_image(image: "Image", path: Path) -> None:
    """Write an image to disk, creating parent directories first."""

    output_path = path.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def _load_pillow_image_module():
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise PreprocessError("Missing Python dependency `Pillow`. Run `uv sync` to install it.") from exc

    return Image
