from __future__ import annotations

import tomllib
from argparse import Namespace

from hyprcam.config import (
    Config,
    default_config_path,
    from_dict,
    load_config,
    overrides_from_args,
    save_config,
)


def test_defaults() -> None:
    config = Config()
    assert config.device == "/dev/video0"
    assert (config.width, config.height, config.fps) == (640, 480, 30)
    assert config.pixel_format == "MJPG"
    assert config.mirror is True
    assert config.floating is False
    assert config.as_dict["float"] is False


def test_load_missing_uses_defaults(tmp_path) -> None:
    assert load_config(tmp_path / "missing.toml") == Config()


def test_save_and_load_roundtrip(tmp_path) -> None:
    path = tmp_path / "nested" / "config.toml"
    config = Config(
        device="/dev/video2",
        width=1280,
        height=720,
        fps=60,
        pixel_format="YUYV",
        mirror=False,
        floating=True,
    )
    written = save_config(config, path)
    assert written == path
    parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    assert parsed == config.as_dict
    assert load_config(path) == config


def test_invalid_values_are_normalised() -> None:
    config = from_dict(
        {
            "width": -4,
            "height": "abc",
            "fps": 0,
            "pixel_format": "mjpg",
            "float": "yes",
            "mirror": "off",
        }
    )
    assert config.width == 640
    assert config.height == 480
    assert config.fps == 30
    assert config.pixel_format == "MJPG"
    assert config.floating is True
    assert config.mirror is False


def test_invalid_toml_falls_back_to_defaults(tmp_path, capsys) -> None:
    path = tmp_path / "bad.toml"
    path.write_text("device = [broken", encoding="utf-8")
    assert load_config(path) == Config()
    assert "ignoring invalid config" in capsys.readouterr().err


def test_overrides_from_args() -> None:
    args = Namespace(device="/dev/video9", width=320, mirror=False, float=True, list_devices=False)
    assert overrides_from_args(args) == {
        "device": "/dev/video9",
        "width": 320,
        "mirror": False,
        "float": True,
    }
    assert Config().with_overrides(overrides_from_args(args)) == Config(
        device="/dev/video9", width=320, mirror=False, floating=True
    )


def test_default_config_path_respects_xdg(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert default_config_path() == tmp_path / "hyprcam" / "config.toml"
