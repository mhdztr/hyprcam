# hyprcam

A minimal webcam window designed for [Hyprland](https://hypr.land/). It opens as a
normal **tiled, frameless** window, so OBS can record your face by capturing a
region of the screen — no OBS camera overlay, no ffplay wrapper, no video mixer
configuration required.

The window has no chrome or controls. Right-click it to open the settings dialog.

## Features

- Direct V4L2 capture through OpenCV (`cv2.VideoCapture` with `CAP_V4L2`); no portal.
- Frameless Qt window that tiles like any other Hyprland client.
- Two window titles for rules: `hyprcam` (tiled) and `hyprcam-float` (floating).
- Settings from both `~/.config/hyprcam/config.toml` and a settings dialog.
- Live apply: device, resolution, FPS, pixel format, mirroring and floating state
  take effect without restarting the app.
- `Super+B` toggles the camera on and off via a pidfile-based launcher.
- Optional floating mode (centred 480×360 by the provided Hyprland rule).

## Installation

### Arch Linux (pacman)

```sh
sudo pacman -S pyside6 python-opencv ruff mypy python-pytest python-build v4l-utils
```

From a checkout:

```sh
cd ~/Projects/hyprcam
chmod +x scripts/hyprcam scripts/hyprcam-toggle
ln -sf "$PWD/scripts/hyprcam" ~/.local/bin/hyprcam
ln -sf "$PWD/scripts/hyprcam-toggle" ~/.local/bin/hyprcam-toggle
```

The wrapper scripts resolve their own real path with `readlink -f`, add `src/`
to `PYTHONPATH`, and exec `python3 -m hyprcam`, so symlinks work without
installing the package. Alternatively install the package with
`pip install -e '.[dev]'` to get `hyprcam` and `hyprcam-toggle` console scripts.

### Hyprland keybinding (Lua config)

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

Then run `hyprctl reload`. The equivalent legacy `.conf` lines are:

```conf
bind = SUPER, B, exec, ~/.local/bin/hyprcam-toggle
windowrulev2 = noborder, class:^hyprcam$
windowrulev2 = float, title:^hyprcam-float$
```

Press `Super+B` to open the tiled camera; press it again to close it.

## Usage

```sh
hyprcam                       # launch with saved defaults
hyprcam --settings            # launch and open the settings dialog
hyprcam --list-devices        # list detected cameras and supported formats
hyprcam --device /dev/video1 --width 1280 --height 720 --fps 30
hyprcam --no-mirror --float   # CLI overrides for this launch only
hyprcam --config /path/to/config.toml
```

Right-click the video window to open settings. Every control applies live;
**Apply** writes the current values back to the TOML file. The settings dialog is
also frameless-free (it uses a normal window decorated by the `hyprcam-settings`
rule).

### Configuration

Location: `~/.config/hyprcam/config.toml` (or `$XDG_CONFIG_HOME/hyprcam/config.toml`).
See [`config.example.toml`](config.example.toml).

```toml
device = "/dev/video0"
width = 640
height = 480
fps = 30
pixel_format = "MJPG"
mirror = true
float = false
```

Precedence: built-in defaults → config file → command-line flags.

`pixel_format` is a four-character FOURCC code. MJPG is tried first (it usually
gives a usable frame rate); YUYV and YUY2 are automatic fallbacks if the camera
rejects it. `float = true` selects the `hyprcam-float` title and the matching
floating rule. When float is toggled in the dialog, hyprcam updates the title and
asks Hyprland to change the window state through `hyprctl dispatch`; if your
Hyprland version rejects that dispatcher, relaunch the window once to pick up
the rule.

### Device discovery

`hyprcam --list-devices` uses `v4l2-ctl --list-devices` (from `v4l-utils`) when
available, including the camera name and supported FOURCC formats. If it is not
installed or the camera is busy, hyprcam probes `/dev/video*` with OpenCV and
reports each device as `available` or `busy or unavailable` instead of failing.

## OBS workflow

1. Open hyprcam with `Super+B`; it tiles on your current workspace.
2. In OBS, add a **Display Capture (Wayland)** or **Window Capture** source.
3. Select/region-capture the tiled hyprcam window and crop to your face.
4. Leave the window tiled and unobstructed — OBS records the tiled feed directly,
   without a separate camera source or overlay.

## Troubleshooting

- **No image / black window**: check `hyprcam --list-devices`; another app may
  have the camera open. Close it and try again.
- **Poor frame rate**: switch `pixel_format` to `MJPG`, or lower width/height/FPS.
- **Window not frameless**: make sure the Lua window rules above are loaded and
  `hyprctl reload` succeeded; verify with `hyprctl clients`.
- **Float change did not take effect**: some Hyprland versions only apply window
  rules at window creation; close and reopen hyprcam.
- **Stale toggle state**: delete `$XDG_RUNTIME_DIR/hyprcam.pid` and press `Super+B`.

## Development

```sh
python3 -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy src
pytest -q
```

CI runs the same checks on Python 3.11–3.13. Pushing a `v*` tag builds an sdist
and wheel and attaches them to a GitHub Release.

## License

MIT © 2026 mhdztr.
