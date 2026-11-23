from __future__ import annotations

from hyprcam import devices
from hyprcam.devices import DeviceInfo, format_devices, list_devices, parse_v4l2ctl_output

SAMPLE = """USB2.0 HD UVC WebCam: USB2.0 HD (usb-0000:00:14.0-7):
\t/dev/video0
\t/dev/video1
\t/dev/media0

Other Camera:
\t/dev/video3
"""


def test_parse_v4l2ctl_output() -> None:
    parsed = parse_v4l2ctl_output(SAMPLE)
    assert [device.path for device in parsed] == ["/dev/video0", "/dev/video1", "/dev/video3"]
    assert parsed[0].name.startswith("USB2.0 HD UVC WebCam")
    assert parsed[2].name == "Other Camera"


def test_format_devices_empty() -> None:
    assert "No webcam devices found" in format_devices([])


def test_format_devices_shows_name_status_and_formats() -> None:
    info = DeviceInfo("/dev/video0", "Webcam", "busy or unavailable", ("MJPG", "YUYV"))
    line = format_devices([info])
    assert line.startswith("/dev/video0 [busy or unavailable]")
    assert "Webcam" in line
    assert "MJPG, YUYV" in line


def test_probe_device_reports_busy(monkeypatch) -> None:
    class FakeCapture:
        def isOpened(self) -> bool:
            return False

        def release(self) -> None:
            return None

    monkeypatch.setattr(devices, "list_formats_v4l2", lambda *args: ("MJPG",))
    info = devices.probe_device("/dev/video9", lambda _: FakeCapture(), "")
    assert info.path == "/dev/video9"
    assert info.status == "busy or unavailable"
    assert info.formats == ("MJPG",)


def test_list_devices_falls_back_to_opencv(monkeypatch) -> None:
    monkeypatch.setattr(devices.glob, "glob", lambda pattern: ["/dev/video7"])
    fake = DeviceInfo("/dev/video7", "Fallback cam", "available")
    monkeypatch.setattr(devices, "probe_device", lambda path, **kwargs: fake)
    assert list_devices("") == [fake]
