"""Settings dialog with live preview of every setting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QHideEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from .config import Config, save_config
from .devices import list_devices

PIXEL_FORMATS = ("MJPG", "YUYV", "YUY2", "NV12", "H264")


class SettingsDialog(QDialog):
    """Edit settings; changes are emitted before ``Apply`` is pressed.

    The parent window connects :attr:`config_changed` to its live-apply handler.
    ``Apply`` persists the current values to the TOML configuration file.
    """

    config_changed = Signal(object)
    saved = Signal(object)

    def __init__(self, config: Config, path: Path, parent: Any | None = None) -> None:
        super().__init__(parent)
        self.path = path
        self.setWindowTitle("hyprcam-settings")
        self.setMinimumWidth(420)

        self.device = QComboBox(self)
        self.device.setEditable(True)
        known = [info.path for info in list_devices()]
        if config.device not in known:
            known.insert(0, config.device)
        self.device.addItems(known)
        self.device.setCurrentText(config.device)

        self.width_spin = QSpinBox(self)
        self.width_spin.setRange(160, 4096)
        self.width_spin.setValue(config.width)
        self.height_spin = QSpinBox(self)
        self.height_spin.setRange(120, 4096)
        self.height_spin.setValue(config.height)
        self.fps_spin = QSpinBox(self)
        self.fps_spin.setRange(1, 240)
        self.fps_spin.setValue(config.fps)

        self.pixel_format = QComboBox(self)
        self.pixel_format.setEditable(True)
        self.pixel_format.addItems(list(PIXEL_FORMATS))
        self.pixel_format.setCurrentText(config.pixel_format)

        self.mirror = QCheckBox("Mirror image horizontally", self)
        self.mirror.setChecked(config.mirror)
        self.floating = QCheckBox("Float the camera window", self)
        self.floating.setChecked(config.floating)

        form = QFormLayout()
        form.addRow("Device", self.device)
        form.addRow("Width", self.width_spin)
        form.addRow("Height", self.height_spin)
        form.addRow("FPS", self.fps_spin)
        form.addRow("Pixel format", self.pixel_format)
        form.addRow("", self.mirror)
        form.addRow("", self.floating)

        self.status = QLabel("Changes apply live. Press Apply to save them.", self)
        self.status.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Close,
            self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.status)
        layout.addWidget(buttons)

        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(350)
        self.preview_timer.timeout.connect(self._emit_preview)

        for widget in (
            self.device,
            self.width_spin,
            self.height_spin,
            self.fps_spin,
            self.pixel_format,
            self.mirror,
            self.floating,
        ):
            self._connect_change_signal(widget)

    def _connect_change_signal(self, widget: Any) -> None:
        for signal_name in ("currentTextChanged", "valueChanged", "toggled", "editTextChanged"):
            signal = getattr(widget, signal_name, None)
            if signal is not None:
                signal.connect(self._schedule_preview)

    def _schedule_preview(self, *_: Any) -> None:
        self.preview_timer.start()

    def _emit_preview(self) -> None:
        self.config_changed.emit(self.current_config())

    def current_config(self) -> Config:
        """Return the configuration currently shown in the dialog."""
        return Config(
            device=self.device.currentText().strip(),
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            fps=self.fps_spin.value(),
            pixel_format=self.pixel_format.currentText().strip().upper(),
            mirror=self.mirror.isChecked(),
            floating=self.floating.isChecked(),
        )

    def save(self) -> Path:
        """Persist the current settings and notify listeners."""
        config = self.current_config()
        written = save_config(config, self.path)
        self.status.setText(f"Saved to {written}")
        self.saved.emit(written)
        return written

    def hideEvent(self, event: QHideEvent) -> None:
        self.preview_timer.stop()
        super().hideEvent(event)
