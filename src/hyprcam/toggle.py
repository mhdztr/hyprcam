"""Launch/stop hyprcam from a single keybinding using a runtime pidfile."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path

PID_NAME = "hyprcam.pid"


def runtime_dir() -> Path:
    """Return the XDG runtime directory (or a temporary fallback)."""
    return Path(os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir())


def pid_path() -> Path:
    """Return the path of hyprcam's pidfile."""
    return runtime_dir() / PID_NAME


def read_pid(path: Path | None = None) -> int | None:
    """Read a live hyprcam PID from the pidfile, pruning stale entries."""
    target = path or pid_path()
    try:
        pid = int(target.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    if pid <= 0 or not process_is_hyprcam(pid):
        target.unlink(missing_ok=True)
        return None
    return pid


def process_is_hyprcam(pid: int) -> bool:
    """Check that ``pid`` still refers to a hyprcam process."""
    try:
        os.kill(pid, 0)
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().lower()
    except (OSError, ProcessLookupError):
        return False
    return b"hyprcam" in cmdline


def start(path: Path | None = None) -> int:
    """Start hyprcam detached and write its PID."""
    target = path or pid_path()
    launcher = Path.home() / ".local" / "bin" / "hyprcam"
    command = [str(launcher)] if launcher.is_file() else [sys.executable, "-m", "hyprcam"]
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"{process.pid}\n", encoding="utf-8")
    return process.pid


def stop(path: Path | None = None) -> bool:
    """Terminate the running instance, if any."""
    target = path or pid_path()
    pid = read_pid(target)
    if pid is None:
        return False
    try:
        os.kill(pid, 15)
        for _ in range(20):
            if not process_is_hyprcam(pid):
                break
            time.sleep(0.05)
    except OSError:
        pass
    target.unlink(missing_ok=True)
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Toggle hyprcam: stop it when running, otherwise start it."""
    parser = argparse.ArgumentParser(
        prog="hyprcam-toggle", description="Toggle the hyprcam camera window."
    )
    parser.parse_args(argv)
    if stop():
        print("hyprcam stopped")
        return 0
    pid = start()
    print(f"hyprcam started (pid {pid})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
