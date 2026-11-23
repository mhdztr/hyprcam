from __future__ import annotations

from typing import Any

from hyprcam import toggle
from hyprcam.__main__ import build_parser, main
from hyprcam.config import Config, save_config
from hyprcam.devices import DeviceInfo


def test_list_devices_does_not_start_gui(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "hyprcam.__main__.list_devices",
        lambda: [DeviceInfo("/dev/video0", "Webcam", "available", ("MJPG",))],
    )
    monkeypatch.setattr("hyprcam.__main__.run_gui", lambda *a, **k: 99)
    assert main(["--list-devices"]) == 0
    output = capsys.readouterr().out
    assert "/dev/video0 [available]" in output
    assert "MJPG" in output


def test_config_file_then_cli_overrides(monkeypatch, tmp_path) -> None:
    path = tmp_path / "config.toml"
    save_config(Config(device="/dev/video1", width=800), path)
    captured: dict[str, Any] = {}

    def fake_gui(config: Config, config_path: Any, show_settings: bool) -> int:
        captured.update(config=config, path=config_path, settings=show_settings)
        return 0

    monkeypatch.setattr("hyprcam.__main__.run_gui", fake_gui)
    assert main(["--config", str(path), "--width", "1280", "--no-mirror", "--float"]) == 0
    config = captured["config"]
    assert config.device == "/dev/video1"
    assert config.width == 1280
    assert config.height == 480
    assert config.mirror is False
    assert config.floating is True
    assert captured["path"] == path
    assert captured["settings"] is False


def test_bool_flags_default_to_none() -> None:
    args = build_parser().parse_args([])
    assert args.mirror is None
    assert args.float is None
    args = build_parser().parse_args(["--mirror", "--no-float"])
    assert args.mirror is True
    assert args.float is False


def test_read_pid_prunes_stale_entry(monkeypatch, tmp_path) -> None:
    path = tmp_path / "hyprcam.pid"
    path.write_text("999999\n", encoding="utf-8")
    monkeypatch.setattr(toggle, "process_is_hyprcam", lambda pid: False)
    assert toggle.read_pid(path) is None
    assert not path.exists()


def test_toggle_starts_then_stops(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    commands: list[list[str]] = []

    class FakePopen:
        pid = 4242

        def __init__(self, command: list[str], **kwargs: Any) -> None:
            commands.append(command)

    monkeypatch.setattr(toggle.subprocess, "Popen", FakePopen)
    states = iter([True, True, False])
    monkeypatch.setattr(toggle, "process_is_hyprcam", lambda pid: next(states))
    assert toggle.main([]) == 0
    assert toggle.pid_path().read_text(encoding="utf-8").strip() == "4242"
    assert commands and commands[0][-1].endswith("hyprcam")
    assert toggle.main([]) == 0
    assert not toggle.pid_path().exists()
