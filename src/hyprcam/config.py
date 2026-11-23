"""Configuration loading, validation and persistence.

Configuration precedence is: built-in defaults, then ``config.toml``, then
command-line overrides (see :func:`overrides_from_args`).
"""

from __future__ import annotations

import json
import os
import sys
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "device": "/dev/video0",
    "width": 640,
    "height": 480,
    "fps": 30,
    "pixel_format": "MJPG",
    "mirror": True,
    "float": False,
}


def config_dir() -> Path:
    """Return the directory holding hyprcam's configuration file."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return Path(xdg) / "hyprcam" if xdg else Path.home() / ".config" / "hyprcam"


def default_config_path() -> Path:
    """Return the default path of the TOML configuration file."""
    return config_dir() / "config.toml"


def _as_positive_int(value: Any, fallback: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return number if 0 < number <= 100_000 else fallback


def _as_bool(value: Any, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return fallback


def _as_fourcc(value: Any, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    code = value.strip().upper()
    return code if len(code) == 4 and code.isascii() and code.isalnum() else fallback


def from_dict(values: Mapping[str, Any]) -> Config:
    """Build a :class:`Config`, normalising and validating every field."""
    merged = {**DEFAULTS, **{key: value for key, value in values.items() if key in DEFAULTS}}
    return Config(
        device=str(merged["device"] or DEFAULTS["device"]),
        width=_as_positive_int(merged["width"], DEFAULTS["width"]),
        height=_as_positive_int(merged["height"], DEFAULTS["height"]),
        fps=_as_positive_int(merged["fps"], DEFAULTS["fps"]),
        pixel_format=_as_fourcc(merged["pixel_format"], DEFAULTS["pixel_format"]),
        mirror=_as_bool(merged["mirror"], DEFAULTS["mirror"]),
        floating=_as_bool(merged["float"], DEFAULTS["float"]),
    )


@dataclass(frozen=True, slots=True)
class Config:
    """Validated application settings.

    ``floating`` maps to the ``float`` TOML key because ``float`` is a Python
    keyword.
    """

    device: str = DEFAULTS["device"]
    width: int = DEFAULTS["width"]
    height: int = DEFAULTS["height"]
    fps: int = DEFAULTS["fps"]
    pixel_format: str = DEFAULTS["pixel_format"]
    mirror: bool = DEFAULTS["mirror"]
    floating: bool = DEFAULTS["float"]

    @property
    def as_dict(self) -> dict[str, Any]:
        """Return the settings using their TOML key names."""
        return {
            "device": self.device,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "pixel_format": self.pixel_format,
            "mirror": self.mirror,
            "float": self.floating,
        }

    def with_overrides(self, overrides: Mapping[str, Any]) -> Config:
        """Return a copy with non-``None`` overrides applied."""
        values = self.as_dict
        for key, value in overrides.items():
            if key in values and value is not None:
                values[key] = value
        return from_dict(values)


def load_config(path: Path | None = None) -> Config:
    """Load configuration from ``path`` or the default location."""
    target = path or default_config_path()
    try:
        with target.open("rb") as handle:
            raw = tomllib.load(handle)
    except FileNotFoundError:
        return Config()
    except (OSError, tomllib.TOMLDecodeError) as exc:
        print(f"hyprcam: ignoring invalid config {target}: {exc}", file=sys.stderr)
        return Config()
    return from_dict(raw)


def save_config(config: Config, path: Path | None = None) -> Path:
    """Write ``config`` as TOML and return the path that was written."""
    target = path or default_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    values = config.as_dict
    lines = ["# hyprcam configuration", "# Managed by hyprcam --settings"]
    for key, default in DEFAULTS.items():
        value = values[key]
        if isinstance(default, bool):
            rendered = "true" if value else "false"
        elif isinstance(default, str):
            rendered = json.dumps(str(value))
        else:
            rendered = str(value)
        lines.append(f"{key} = {rendered}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def overrides_from_args(args: Any) -> dict[str, Any]:
    """Extract configuration overrides from parsed command-line arguments."""
    return {
        key: value for key, value in vars(args).items() if key in DEFAULTS and value is not None
    }
