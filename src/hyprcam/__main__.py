"""Command-line entry point and the frameless camera window."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QContextMenuEvent, QPixmap
from PySide6.QtWidgets import QApplication, QLabel

from .camera import CameraThread
from .config import Config, default_config_path, load_config, overrides_from_args
from .devices import format_devices, list_devices
from .settings_dialog import SettingsDialog

TILED_TITLE = "hyprcam"
FLOATING_TITLE = "hyprcam-float"
CAPTURE_KEYS = ("device", "width", "height", "fps", "pixel_format", "mirror")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for ``hyprcam``."""
    parser = argparse.ArgumentParser(
        prog="hyprcam",
        description="Minimal frameless webcam window that tiles in Hyprland.",
    )
    parser.add_argument("--list-devices", action="store_true", help="list V4L2 cameras and exit")
    parser.add_argument("--settings", action="store_true", help="open the settings dialog")
    parser.add_argument("--device", help="V4L2 device path, e.g. /dev/video0")
    parser.add_argument("--width", type=int, help="requested capture width")
    parser.add_argument("--height", type=int, help="requested capture height")
    parser.add_argument("--fps", type=int, help="requested capture frame rate")
    parser.add_argument("--pixel-format", dest="pixel_format", help="FOURCC, e.g. MJPG or YUYV")
    parser.add_argument(
        "--mirror", dest="mirror", action="store_true", default=None, help="mirror the image"
    )
    parser.add_argument(
        "--no-mirror", dest="mirror", action="store_false", help="do not mirror the image"
    )
    parser.add_argument(
        "--float", dest="float", action="store_true", default=None, help="use a floating window"
    )
    parser.add_argument("--no-float", dest="float", action="store_false", help="use a tiled window")
    parser.add_argument("--config", type=Path, help="path to an alternative config.toml")
    return parser


def apply_hyprland_float(floating: bool) -> str | None:
    """Switch the window's floating state via Hyprland IPC.

    Hyprland applies window rules at window creation, so a live change is sent
    through ``hyprctl dispatch``. Returns an error message if every dispatcher
    spelling fails (in which case relaunching the window may be required).
    """
    selector = FLOATING_TITLE if floating else TILED_TITLE
    value = str(floating).lower()
    lua = f'hl.dsp.window.float({{ window = "title:{selector}", floating = {value} }})'
    commands = [
        ["hyprctl", "dispatch", lua],
        [
            "hyprctl",
            "dispatch",
            f"setfloating title:{selector}" if floating else f"settiled title:{selector}",
        ],
    ]
    errors: list[str] = []
    for command in commands:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=4, check=False)
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(str(exc))
            continue
        output = f"{result.stdout} {result.stderr}".strip().lower()
        if result.returncode == 0 and "error" not in output:
            return None
        errors.append(output or f"exit status {result.returncode}")
    return "; ".join(errors) or "hyprctl dispatch failed"


class CameraWindow(QLabel):
    """A frameless QLabel that displays live camera frames."""

    def __init__(self, config: Config, config_path: Path, parent: Any | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.config_path = config_path
        self.settings_dialog: SettingsDialog | None = None

        self.setWindowTitle(self.title_for(config))
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: black; color: white;")
        self.setMinimumSize(160, 120)
        self.resize(config.width, config.height)

        self.camera = self._new_camera(config)
        self.camera.start()

    @staticmethod
    def title_for(config: Config) -> str:
        """Return the window title that selects the matching Hyprland rule."""
        return FLOATING_TITLE if config.floating else TILED_TITLE

    def _new_camera(self, config: Config) -> CameraThread:
        thread = CameraThread(config, self)
        thread.frame_ready.connect(self.show_frame)
        thread.error.connect(self.show_error)
        return thread

    def show_frame(self, image: Any) -> None:
        """Scale a frame to the window while preserving its aspect ratio."""
        scaled = image.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(QPixmap.fromImage(scaled))

    def show_error(self, message: str) -> None:
        """Show a concise error message inside the frameless window."""
        self.setText(f"hyprcam: {message}")

    def apply_config(self, config: Config) -> None:
        """Apply live settings changes from the dialog."""
        previous = self.config
        self.config = config
        if previous.floating != config.floating:
            self.setWindowTitle(self.title_for(config))
            QTimer.singleShot(
                250, lambda: self._report_float_result(apply_hyprland_float(config.floating))
            )
        if any(getattr(previous, key) != getattr(config, key) for key in CAPTURE_KEYS):
            self.camera.stop()
            self.camera = self._new_camera(config)
            self.camera.start()

    def _report_float_result(self, error: str | None) -> None:
        if error:
            self.show_error(f"float change needs a window restart ({error})")

    def open_settings(self) -> None:
        """Show the settings dialog, reusing it if it is already open."""
        if self.settings_dialog is None:
            dialog = SettingsDialog(self.config, self.config_path, self)
            dialog.config_changed.connect(self.apply_config)
            dialog.finished.connect(lambda: setattr(self, "settings_dialog", None))
            self.settings_dialog = dialog
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self.open_settings()
        event.accept()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.camera.stop()
        super().closeEvent(event)


def run_gui(config: Config, config_path: Path, show_settings: bool) -> int:
    """Start the Qt application and show the camera window."""
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("hyprcam")
    window = CameraWindow(config, config_path)
    window.show()
    if show_settings:
        window.open_settings()
    return int(application.exec())


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, handle information flags, then launch the GUI."""
    args = build_parser().parse_args(argv)
    if args.list_devices:
        print(format_devices(list_devices()))
        return 0

    config_path = args.config or default_config_path()
    config = load_config(config_path).with_overrides(overrides_from_args(args))
    return run_gui(config, config_path, args.settings)


if __name__ == "__main__":
    raise SystemExit(main())
