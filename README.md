# hyprcam

[![CI](https://github.com/mhdztr/hyprcam/actions/workflows/ci.yml/badge.svg)](https://github.com/mhdztr/hyprcam/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/mhdztr/hyprcam)](https://github.com/mhdztr/hyprcam/releases)
[![License: MIT](https://img.shields.io/github/license/mhdztr/hyprcam)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpypi.org%2Fpypi%2Fhyprcam%2Fjson&query=%24.info.version&label=PyPI)](https://pypi.org/project/hyprcam/)
[![AUR](https://img.shields.io/aur/version/hyprcam)](https://aur.archlinux.org/packages/hyprcam)

> The PyPI badge reads live PyPI metadata and shows 0.2.1; the AUR badge shows
> "not found" until the AUR package is submitted. Badge providers may cache
> briefly.

A minimal webcam window for [Hyprland](https://hypr.land/). It opens as a normal
**tiled, frameless** window, so OBS can capture your face by recording a region
of the screen — no virtual camera, no OBS overlay, no `ffplay` wrapper, no video
mixer configuration.

The video window has no chrome or controls. Right-click it (or use
`hyprcam --settings`) to open the settings dialog.

> **Status:** early-stage (v0.2.1), Linux/V4L2 only. PyPI publishing is live;
> AUR packaging is prepared but not submitted yet. See
> [Installation](#installation) and [Publishing](#publishing-maintainers).

## Contents

- [Highlights](#highlights)
- [Requirements](#requirements)
- [Installation](#installation)
- [Hyprland setup](#hyprland-setup)
- [Usage](#usage)
- [Configuration](#configuration)
- [Device discovery](#device-discovery)
- [OBS workflow](#obs-workflow)
- [Screenshots](#screenshots)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Publishing (maintainers)](#publishing-maintainers)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Highlights

- **Direct V4L2 capture** through OpenCV (`cv2.VideoCapture` with `CAP_V4L2`); no
  portal or PipeWire virtual device needed.
- **Tiled by default.** The frameless window behaves like any other Hyprland
  client, so it is easy to region-capture from OBS.
- **Two window titles for rules:** `hyprcam` (tiled) and `hyprcam-float`
  (floating). The settings dialog uses `hyprcam-settings`.
- **Settings that apply live.** Device, resolution, FPS, pixel format, mirroring
  and floating state update without restarting; **Apply** saves them to TOML.
- **CLI overrides** for one-off launches, on top of a validated config file with
  sane defaults.
- **Single-key toggle.** `hyprcam-toggle` uses a pidfile in `$XDG_RUNTIME_DIR`
  and works with a `Super+B` binding.
- **Device discovery.** `hyprcam --list-devices` uses `v4l2-ctl` when available,
  with an OpenCV `/dev/video*` probe fallback.
- **Small, testable core.** 17 tests cover config, CLI and device discovery; CI
  runs lint, format, type checks and tests on Python 3.11–3.13.

## Requirements

- Linux with a V4L2 webcam exposed as `/dev/video*`.
- Python 3.11 or newer.
- Qt 6 via PySide6 and OpenCV (installed by pip, or from Arch system packages).
- Hyprland for the suggested keybinding and window rules. The Qt window itself
  also runs on other Wayland/X11 desktops, but the rules and `hyprctl` calls are
  Hyprland-specific.
- Optional: `v4l-utils` for detailed device and format reporting.

## Installation

Pick one path. All of them provide the same `hyprcam` and `hyprcam-toggle`
commands.

### Arch Linux / AUR packaging

AUR-ready files live in [`packaging/aur/`](packaging/aur/) (`PKGBUILD`,
`.SRCINFO` and submission notes). **No AUR package has been submitted yet**
(AUR registration is currently closed), so build and install it locally for now:

```sh
sudo pacman -S --needed base-devel
git clone https://github.com/mhdztr/hyprcam.git
cd hyprcam/packaging/aur
makepkg -si
```

The package builds from the `v0.2.1` source tarball with
`python -m build --wheel --no-isolation` and installs the wheel with
`python -m installer`, using Arch's system `pyside6`, `python-opencv` and
`python` packages. Once a package is listed on AUR, the usual
`yay -S hyprcam` (or another AUR helper) will work instead. See
[`packaging/aur/AUR-README.md`](packaging/aur/AUR-README.md) for the exact
submission commands.

### pip / PyPI

Install from [PyPI](https://pypi.org/project/hyprcam/):

```sh
python3 -m pip install hyprcam
hyprcam --list-devices
```

PyPI serves the current `0.2.1` release.

The tagged Git source can also be installed directly:

```sh
python3 -m pip install 'git+https://github.com/mhdztr/hyprcam.git@v0.2.1'
```

A virtual environment is recommended (`python3 -m venv .venv && . .venv/bin/activate`).

### Source checkout (Arch system packages)

Install the runtime libraries from pacman, then run the idempotent user
installer from a checkout:

```sh
sudo pacman -S pyside6 python-opencv v4l-utils
git clone https://github.com/mhdztr/hyprcam.git
cd hyprcam
chmod +x scripts/hyprcam-install-user
./scripts/hyprcam-install-user
```

It creates `~/.local/bin/hyprcam` and `~/.local/bin/hyprcam-toggle` symlinks,
installs `hyprcam.desktop` into `~/.local/share/applications/`, and seeds
`~/.config/hyprcam/config.toml` from `config.example.toml` without overwriting
an existing config. Re-running it is safe; if `~/.local/bin` is not on `PATH`, it
prints a warning instead of failing.

Make sure `~/.local/bin` is on your `PATH`, or `hyprcam` only works by full path
and the desktop entry's `Exec=hyprcam` will fail. For zsh, uncomment (or add)
this line in `~/.zshrc`, above the Oh My Zsh setup:

```sh
export PATH=$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH
```

For fish, add this near the top of `~/.config/fish/config.fish`:

```fish
fish_add_path $HOME/.local/bin
```

Open a new shell (or re-login) and confirm `command -v hyprcam` prints a path.
Desktop environments pick up the installed `.desktop` file on next login;
`update-desktop-database ~/.local/share/applications` refreshes it immediately.

The wrapper scripts resolve their own real path with `readlink -f`, add `src/`
to `PYTHONPATH`, and exec `python3 -m hyprcam`, so symlinks work without
installing the package. Alternatively use an editable install for development:

```sh
python3 -m pip install -e '.[dev]'
```

## Hyprland setup

Add a variable in `variables.lua` under `-- Apps`:

```lua
kbHyprcam = "SUPER + B",
```

Add the bind in `hyprland/keybinds.lua` under `-- Apps`:

```lua
create_bind(vars.kbHyprcam, hl.dsp.exec_cmd("~/.local/bin/hyprcam-toggle"))
```

Add the rules in `hyprland/rules.lua` under `-- Per app rules`:

```lua
-- hyprcam: frameless tiled camera window; floating variant selected by title
hl.window_rule({ match = { title = "^hyprcam$" },       border_size = 0, tile = true })
hl.window_rule({ match = { title = "^hyprcam-float$" }, border_size = 0, float = true, size = "480 360", center = true })
hl.window_rule({ match = { title = "^hyprcam-settings$" }, float = true, size = "520 420", center = true })
```

Then run `hyprctl reload` and confirm `hyprctl configerrors` is clean. The
equivalent legacy `.conf` lines are:

```conf
bind = SUPER, B, exec, ~/.local/bin/hyprcam-toggle
windowrulev2 = noborder, class:^hyprcam$
windowrulev2 = float, title:^hyprcam-float$
```

Press `Super+B` to open the tiled camera; press it again to close it.

## Usage

```sh
hyprcam                                              # launch with saved defaults
hyprcam --settings                                   # launch and open settings
hyprcam --list-devices                               # list cameras and formats
hyprcam --device /dev/video1 --width 1280 --height 720 --fps 30
hyprcam --pixel-format YUYV --no-mirror              # FOURCC and mirroring
hyprcam --float                                      # floating variant for this launch
hyprcam --no-float                                   # force tiled variant
hyprcam --config /path/to/config.toml                # alternative config file
hyprcam-toggle                                       # same action as Super+B
```

Right-click the video window to open settings. Changes in the dialog apply
live; **Apply** writes the current values back to the TOML file. The dialog has
a normal decorated window (title `hyprcam-settings`) and is placed by the rule
above.

## Configuration

Location: `~/.config/hyprcam/config.toml`, or
`$XDG_CONFIG_HOME/hyprcam/config.toml` when that variable is set. See
[`config.example.toml`](config.example.toml). The user installer seeds this file
on first run; until then hyprcam uses built-in defaults.

```toml
device = "/dev/video0"
width = 640
height = 480
fps = 30
pixel_format = "MJPG"
mirror = true
float = false
```

| Key | Default | Meaning |
| --- | --- | --- |
| `device` | `/dev/video0` | V4L2 device path; see `hyprcam --list-devices`. |
| `width` | `640` | Requested capture width (160–4096 in the dialog). |
| `height` | `480` | Requested capture height (120–4096 in the dialog). |
| `fps` | `30` | Requested frame rate (1–240 in the dialog). |
| `pixel_format` | `MJPG` | Four-character FOURCC code. |
| `mirror` | `true` | Flip the image horizontally. |
| `float` | `false` | Tiled `hyprcam` window; `true` selects `hyprcam-float`. |

Precedence: **built-in defaults → config file → command-line flags**. Invalid or
missing values fall back to defaults rather than crashing the app.

`pixel_format` is a four-character FOURCC code. The requested format is tried
first; MJPG, YUYV and YUY2 are then tried as fallbacks (MJPG usually gives a
usable frame rate). The settings dialog offers MJPG, YUYV, YUY2, NV12 and H264.

When float is toggled in the dialog, hyprcam updates the title and asks Hyprland
to change the window state via `hyprctl dispatch`. If your Hyprland version
rejects that dispatcher, close and reopen the window once to pick up the rule.

## Device discovery

```text
$ hyprcam --list-devices
/dev/video0 [available] (Integrated Camera, formats: MJPG, YUYV)
```

`hyprcam --list-devices` uses `v4l2-ctl --list-devices` (from `v4l-utils`) when
available, including the camera name and supported FOURCC formats. If it is not
installed or the camera is busy, hyprcam probes `/dev/video*` with OpenCV and
reports each device as `available` or `busy or unavailable` instead of failing.

## OBS workflow

1. Open hyprcam with `Super+B` (or `hyprcam`); it tiles on your current workspace.
2. In OBS, add a **Display Capture (Wayland)** or **Window Capture** source.
3. Select/region-capture the tiled hyprcam window and crop to your face.
4. Leave the window tiled and unobstructed — OBS records the tiled feed
   directly, without a separate camera source or overlay.

For best results, request a capture size that matches your OBS canvas (for
example 1280×720 at 30 FPS via config or CLI flags) and use MJPG if your camera
supports it. hyprcam does not create a virtual camera device and does not
record or stream anything itself.

## Screenshots

No screenshots are bundled yet. To add one for a future release: launch hyprcam
in tiled mode, run `grim -g "$(slurp)" docs/screenshots/tiled.png` (requires
`grim` and `slurp`), and commit the image with a short caption. For the settings
dialog, run `hyprcam --settings` first and repeat the capture.

## Troubleshooting

- **No image / black window**: check `hyprcam --list-devices`; another app may
  have the camera open. Close it and try again.
- **Poor frame rate**: switch `pixel_format` to `MJPG`, or lower width, height
  or FPS.
- **Window not frameless**: make sure the Lua window rules above are loaded and
  `hyprctl reload` succeeded; verify with `hyprctl clients` and
  `hyprctl configerrors`.
- **Float change did not take effect**: some Hyprland versions only apply window
  rules at window creation; close and reopen hyprcam.
- **Stale toggle state**: delete `$XDG_RUNTIME_DIR/hyprcam.pid` and press
  `Super+B` again. The toggle prefers `~/.local/bin/hyprcam`, then falls back to
  `python3 -m hyprcam`.
- **`Exec=hyprcam` fails from the desktop entry**: `~/.local/bin` is missing
  from `PATH` in the desktop session; see the PATH notes above and re-login.
- **`hyprcam --list-devices` shows only `/dev/video*` with no name**: install
  `v4l-utils` for detailed names and formats; the OpenCV fallback still works.

## FAQ

**Is this a virtual camera for OBS?** No. It is a real window that you capture
with OBS Display/Window Capture. It does not use `v4l2loopback` or expose a new
`/dev/video*` device.

**Does it work outside Hyprland?** The Qt window and V4L2 capture can run on
other Linux desktops, but the toggle keybinding, window rules and float
dispatcher are Hyprland-specific. There is no xdg-desktop-portal fallback yet.

**Does hyprcam record, stream or apply effects?** No. It only displays live
frames. Mirroring is the only image transform today.

**Can I open two cameras at once?** Not yet. One device per process; per-device
profiles are on the feature ideas list.

**Is it on AUR or PyPI?** PyPI serves version 0.2.1; use
`python3 -m pip install hyprcam`. AUR packaging is included but has not been
submitted yet. See below.

**Why does my camera reject the requested resolution?** Cameras only support
discrete modes; OpenCV may silently pick a nearby one. Use
`hyprcam --list-devices` to see supported formats and try MJPG/YUYV with a
smaller size.

## Publishing (maintainers)

Pushing a `v*` tag always builds an sdist and wheel and attaches them to a
GitHub Release via `.github/workflows/release.yml`.

PyPI publishing is opt-in so the workflow never fails before it is configured:

1. Create/verify a PyPI account at <https://pypi.org/account/register/>.
2. In the GitHub repository, go to **Settings → Secrets and variables →
   Actions → Variables → New repository variable** and create
   `ENABLE_PYPI_PUBLISH` with value `true`. Until this exists, the PyPI job is
   skipped.
3. On PyPI, open <https://pypi.org/manage/account/publishing/> and add a
   **trusted publisher** with: PyPI Project Name `hyprcam`, Owner `mhdztr`,
   Repository `hyprcam`, Workflow `Publish to PyPI`, Environment `pypi`.
4. Push a new tag, for example
   `git tag -a v0.3.0 -m "hyprcam v0.3.0" && git push origin v0.3.0`. The
   `pypi` environment is created on first use. PyPI filenames are immutable;
   bump the version for each new release.

The current published release is v0.2.1.

The workflow uses `pypa/gh-action-pypi-publish@release/v1` with OIDC
(`id-token: write`); no PyPI token is stored in the repository.

## Development

```sh
python3 -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy src
pytest -q
```

If the tools are installed but not on `PATH`, prefix with `python3 -m` (for
example `python3 -m ruff check .`). CI runs the same checks on Python 3.11–3.13
with `QT_QPA_PLATFORM=offscreen`; tests do not need a camera.

## Contributing

Bug reports, feature requests and pull requests are welcome. Start with
[`CONTRIBUTING.md`](CONTRIBUTING.md), the
[issue templates](.github/ISSUE_TEMPLATE/), the
[pull request template](.github/PULL_REQUEST_TEMPLATE.md), the
[changelog](CHANGELOG.md) and the [code of conduct](CODE_OF_CONDUCT.md).

## License

MIT © 2026 mhdztr. See [LICENSE](LICENSE).
