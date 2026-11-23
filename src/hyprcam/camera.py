"""OpenCV V4L2 capture running in a Qt worker thread."""

from __future__ import annotations

from typing import Any

import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from .config import Config

FALLBACK_FORMATS = ("MJPG", "YUYV", "YUY2")


def fourcc(code: str) -> int:
    """Pack a four-character pixel-format code the way OpenCV's FOURCC does."""
    return sum(ord(character) << (8 * index) for index, character in enumerate(code))


def open_capture(config: Config) -> tuple[Any, str]:
    """Open a V4L2 capture, trying the requested format before the fallbacks."""
    candidates = list(dict.fromkeys((config.pixel_format, *FALLBACK_FORMATS)))
    last_error = ""
    for code in candidates:
        capture = cv2.VideoCapture(config.device, cv2.CAP_V4L2)
        capture.set(cv2.CAP_PROP_FOURCC, fourcc(code))
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)
        capture.set(cv2.CAP_PROP_FPS, config.fps)
        if capture.isOpened():
            return capture, code
        last_error = f" (tried {code})"
        capture.release()
    raise RuntimeError(f"Could not open {config.device} with OpenCV/V4L2{last_error}")


def frame_to_qimage(frame: Any, mirror: bool) -> QImage:
    """Convert an OpenCV BGR frame to an owned RGB QImage."""
    working = cv2.flip(frame, 1) if mirror else frame
    conversion = cv2.COLOR_BGRA2RGB if working.shape[2] == 4 else cv2.COLOR_BGR2RGB
    rgb = cv2.cvtColor(working, conversion)
    height, width, channels = rgb.shape
    image = QImage(
        rgb.data,
        width,
        height,
        channels * width,
        QImage.Format.Format_RGB888,
    )
    return image.copy()


class CameraThread(QThread):
    """Capture frames and emit them as QImages until stopped."""

    frame_ready = Signal(QImage)
    error = Signal(str)
    format_selected = Signal(str)

    def __init__(self, config: Config, parent: Any | None = None) -> None:
        super().__init__(parent)
        self.config = config

    def run(self) -> None:
        """Open the camera and emit frames until interruption or failure."""
        try:
            capture, selected_format = open_capture(self.config)
        except Exception as exc:
            self.error.emit(str(exc))
            return

        self.format_selected.emit(selected_format)
        failures = 0
        try:
            while not self.isInterruptionRequested():
                ok, frame = capture.read()
                if not ok or frame is None:
                    failures += 1
                    if failures >= 25:
                        self.error.emit("Camera stopped delivering frames.")
                        break
                    self.msleep(40)
                    continue
                failures = 0
                try:
                    image = frame_to_qimage(frame, self.config.mirror)
                except Exception as exc:
                    self.error.emit(f"Could not process camera frame: {exc}")
                    break
                self.frame_ready.emit(image)
                self.msleep(5)
        finally:
            capture.release()

    def stop(self) -> None:
        """Ask the thread to stop and wait for it to finish."""
        if not self.isRunning():
            return
        self.requestInterruption()
        if not self.wait(2000):
            self.terminate()
            self.wait(1000)
