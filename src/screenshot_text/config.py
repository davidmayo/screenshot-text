"""Configuration loading, validation, and persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "screenshot-text" / "config.toml"


class ConfigError(RuntimeError):
    """Raised when the config file is invalid or incomplete."""


@dataclass(slots=True)
class RegionConfig:
    """Screen coordinates for a rectangular capture area."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ConfigError("Region width and height must be greater than zero.")


@dataclass(slots=True)
class OcrConfig:
    """OCR settings passed through to Tesseract."""

    lang: str = "eng"
    psm: int = 6

    def __post_init__(self) -> None:
        if not self.lang.strip():
            raise ConfigError("OCR language cannot be empty.")
        if self.psm <= 0:
            raise ConfigError("OCR page segmentation mode must be greater than zero.")


@dataclass(slots=True)
class PreprocessConfig:
    """Image preprocessing settings used before OCR."""

    grayscale: bool = True
    upscale: int = 2
    threshold: int = 180
    invert: bool = False

    def __post_init__(self) -> None:
        if self.upscale <= 0:
            raise ConfigError("Preprocess upscale must be greater than zero.")
        if not 0 <= self.threshold <= 255:
            raise ConfigError("Preprocess threshold must be between 0 and 255.")


@dataclass(slots=True)
class DetectionConfig:
    """Debounce settings for deciding whether OCR text is worth accepting."""

    require_stable_reads: int = 1

    def __post_init__(self) -> None:
        if self.require_stable_reads <= 0:
            raise ConfigError("Detection require_stable_reads must be greater than zero.")


@dataclass(slots=True)
class DebugConfig:
    """Optional debug output paths."""

    save_dir: Path | None = None


@dataclass(slots=True)
class AppConfig:
    """Whole-application configuration."""

    interval_seconds: float = 2.0
    region: RegionConfig | None = None
    ocr: OcrConfig = field(default_factory=OcrConfig)
    preprocess: PreprocessConfig = field(default_factory=PreprocessConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ConfigError("interval_seconds must be greater than zero.")


def load_config(path: Path) -> AppConfig:
    """Load config from TOML, or return defaults when the file does not exist."""

    config_path = path.expanduser()
    if not config_path.exists():
        return AppConfig()

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return AppConfig()
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Could not parse config file {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Config file {config_path} must contain a TOML table.")

    interval_seconds = _coerce_float(
        data.get("interval_seconds", 2.0),
        "interval_seconds",
    )

    region = None
    if "region" in data:
        region = _parse_region(_require_table(data["region"], "region"))

    ocr = _parse_ocr(_optional_table(data, "ocr"))
    preprocess = _parse_preprocess(_optional_table(data, "preprocess"))
    detection = _parse_detection(_optional_table(data, "detection"))
    debug = _parse_debug(_optional_table(data, "debug"))

    return AppConfig(
        interval_seconds=interval_seconds,
        region=region,
        ocr=ocr,
        preprocess=preprocess,
        detection=detection,
        debug=debug,
    )


def save_config(config: AppConfig, path: Path) -> None:
    """Persist config to TOML, creating parent directories when needed."""

    config_path = path.expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(render_config(config), encoding="utf-8")


def render_config(config: AppConfig) -> str:
    """Render config as a small TOML document."""

    lines = [f"interval_seconds = {config.interval_seconds}", ""]

    if config.region is not None:
        lines.extend(
            [
                "[region]",
                f"x = {config.region.x}",
                f"y = {config.region.y}",
                f"width = {config.region.width}",
                f"height = {config.region.height}",
                "",
            ]
        )

    lines.extend(
        [
            "[ocr]",
            f'lang = "{_quote(config.ocr.lang)}"',
            f"psm = {config.ocr.psm}",
            "",
            "[preprocess]",
            f"grayscale = {_toml_bool(config.preprocess.grayscale)}",
            f"upscale = {config.preprocess.upscale}",
            f"threshold = {config.preprocess.threshold}",
            f"invert = {_toml_bool(config.preprocess.invert)}",
            "",
            "[detection]",
            f"require_stable_reads = {config.detection.require_stable_reads}",
            "",
        ]
    )

    if config.debug.save_dir is not None:
        lines.extend(
            [
                "[debug]",
                f'save_dir = "{_quote(str(config.debug.save_dir))}"',
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _parse_region(table: dict[str, object]) -> RegionConfig:
    return RegionConfig(
        x=_coerce_int(table.get("x"), "region.x"),
        y=_coerce_int(table.get("y"), "region.y"),
        width=_coerce_int(table.get("width"), "region.width"),
        height=_coerce_int(table.get("height"), "region.height"),
    )


def _parse_ocr(table: dict[str, object] | None) -> OcrConfig:
    if table is None:
        return OcrConfig()

    return OcrConfig(
        lang=_coerce_string(table.get("lang", "eng"), "ocr.lang"),
        psm=_coerce_int(table.get("psm", 6), "ocr.psm"),
    )


def _parse_preprocess(table: dict[str, object] | None) -> PreprocessConfig:
    if table is None:
        return PreprocessConfig()

    return PreprocessConfig(
        grayscale=_coerce_bool(table.get("grayscale", True), "preprocess.grayscale"),
        upscale=_coerce_int(table.get("upscale", 2), "preprocess.upscale"),
        threshold=_coerce_int(table.get("threshold", 180), "preprocess.threshold"),
        invert=_coerce_bool(table.get("invert", False), "preprocess.invert"),
    )


def _parse_detection(table: dict[str, object] | None) -> DetectionConfig:
    if table is None:
        return DetectionConfig()

    return DetectionConfig(
        require_stable_reads=_coerce_int(
            table.get("require_stable_reads", 1),
            "detection.require_stable_reads",
        )
    )


def _parse_debug(table: dict[str, object] | None) -> DebugConfig:
    if table is None:
        return DebugConfig()

    save_dir = table.get("save_dir")
    if save_dir is None:
        return DebugConfig()

    return DebugConfig(save_dir=Path(_coerce_string(save_dir, "debug.save_dir")).expanduser())


def _optional_table(data: dict[str, object], key: str) -> dict[str, object] | None:
    value = data.get(key)
    if value is None:
        return None
    return _require_table(value, key)


def _require_table(value: object, key: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be a TOML table.")
    return value


def _coerce_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{field_name} must be an integer.")
    return value


def _coerce_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{field_name} must be a number.")
    return float(value)


def _coerce_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{field_name} must be true or false.")
    return value


def _coerce_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{field_name} must be a string.")
    return value


def _toml_bool(value: bool) -> str:
    return "true" if value else "false"


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
