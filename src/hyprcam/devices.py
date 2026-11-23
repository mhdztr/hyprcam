"""Webcam discovery via v4l2-ctl, with an OpenCV fallback."""

from __future__ import annotations

import glob
import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FOURCC_RE = re.compile(r"'([A-Za-z0-9]{4})'")


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """One discovered video device."""

    path: str
    name: str = ""
    status: str = "unknown"
    formats: tuple[str, ...] = ()

    def render(self) -> str:
        """Return a single informative terminal line."""
        details: list[str] = []
        if self.name:
            details.append(self.name)
        if self.formats:
            details.append("formats: " + ", ".join(self.formats))
        suffix = f" ({', '.join(details)})" if details else ""
        return f"{self.path} [{self.status}]{suffix}"


def format_devices(devices: list[DeviceInfo]) -> str:
    """Render device discovery results for the command line."""
    if not devices:
        return "No webcam devices found. Check that a V4L2 camera is attached and unlocked."
    return "\n".join(device.render() for device in devices)


def parse_v4l2ctl_output(text: str) -> list[DeviceInfo]:
    """Parse the indented device listing produced by ``v4l2-ctl --list-devices``."""
    devices: list[DeviceInfo] = []
    name = ""
    for line in text.splitlines():
        if not line.strip():
            continue
        if not line[0].isspace():
            name = line.strip().rstrip(":")
            continue
        path = line.strip()
        if path.startswith("/dev/video") and path not in {device.path for device in devices}:
            devices.append(DeviceInfo(path=path, name=name, status="available"))
    return devices


def list_formats_v4l2(path: str, v4l2ctl: str | None = None) -> tuple[str, ...]:
    """Ask v4l2-ctl for supported pixel formats; return an empty tuple on failure."""
    executable = v4l2ctl if v4l2ctl is not None else shutil.which("v4l2-ctl")
    if not executable:
        return ()
    try:
        result = subprocess.run(
            [executable, "-d", path, "--list-formats"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ()
    if result.returncode != 0:
        return ()
    seen: dict[str, None] = {}
    for match in FOURCC_RE.finditer(result.stdout):
        seen.setdefault(match.group(1), None)
    return tuple(seen)


def _sysfs_name(path: str) -> str:
    name_file = Path("/sys/class/video4linux") / Path(path).name / "name"
    try:
        return name_file.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def probe_device(
    path: str,
    capture_factory: Callable[[str], Any] | None = None,
    v4l2ctl: str | None = None,
) -> DeviceInfo:
    """Probe one device with OpenCV when v4l2-ctl cannot describe it."""
    open_capture = capture_factory
    if open_capture is None:
        import cv2  # imported lazily so --list-devices stays fast

        def open_capture(device: str) -> Any:
            return cv2.VideoCapture(device, cv2.CAP_V4L2)

    capture = None
    try:
        capture = open_capture(path)
        opened = bool(capture is not None and capture.isOpened())
    except Exception:  # a busy or exotic device may raise from OpenCV
        opened = False
    finally:
        if capture is not None:
            try:
                capture.release()
            except Exception:
                pass
    status = "available" if opened else "busy or unavailable"
    return DeviceInfo(
        path=path,
        name=_sysfs_name(path),
        status=status,
        formats=list_formats_v4l2(path, v4l2ctl),
    )


def list_devices(v4l2ctl: str | None = None) -> list[DeviceInfo]:
    """List webcams, preferring v4l2-ctl and falling back to OpenCV probing.

    Pass an empty string for ``v4l2ctl`` to force the fallback (used by tests).
    """
    executable = shutil.which("v4l2-ctl") if v4l2ctl is None else v4l2ctl
    if executable:
        try:
            result = subprocess.run(
                [executable, "--list-devices"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            result = None
        if result is not None and result.returncode == 0:
            listed = parse_v4l2ctl_output(result.stdout)
            if listed:
                return [
                    DeviceInfo(
                        path=device.path,
                        name=device.name,
                        status="available",
                        formats=list_formats_v4l2(device.path, executable),
                    )
                    for device in listed
                ]

    return [probe_device(path, v4l2ctl=executable) for path in sorted(glob.glob("/dev/video*"))]
