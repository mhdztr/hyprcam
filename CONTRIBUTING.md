# Contributing to hyprcam

Thanks for taking the time to help. hyprcam is a small Linux desktop app, so the
most useful contributions are usually bug reports with reproducible details,
documentation fixes, and focused code changes.

## Ways to contribute

- **Report a bug** with the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml).
  Include your Hyprland, Qt, Python and camera details, plus the output of
  `hyprcam --list-devices`.
- **Suggest a feature** with the [feature request template](.github/ISSUE_TEMPLATE/feature_request.yml).
  Explain the workflow you are trying to solve, not just the implementation.
- **Improve the docs**: README, config reference, troubleshooting and examples.
- **Send a pull request** for a focused bug fix or feature.

Please read the [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## Development setup

Requirements: Python 3.11 or newer, a V4L2 webcam for manual testing, and (on
Arch) the system packages used by the AUR build:

```sh
sudo pacman -S pyside6 python-opencv v4l-utils ruff mypy python-pytest python-build
```

From a checkout:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e '.[dev]'
```

The wrapper scripts in `scripts/` run straight from the checkout without an
editable install if you prefer that path.

## Checks

Run these before opening a pull request:

```sh
ruff check .
ruff format --check .
mypy src
pytest -q
```

If the tools are installed as Python modules but their console scripts are not
on `PATH`, prefix each command with `python3 -m` (for example
`python3 -m ruff check .`). CI runs the same checks on Python 3.11, 3.12 and
3.13 with `QT_QPA_PLATFORM=offscreen`; unit tests should never require real
camera hardware.

When changing Hyprland rules or keybindings in a personal config, validate it
with `hyprctl reload` and `hyprctl configerrors` before reporting a regression.
The Lua config and legacy `.conf` tree used for local testing are considered
working and should not be changed as part of unrelated PRs.

## Pull requests

1. Fork the repository and create a topic branch from `main`.
2. Keep each commit focused and use a one-line conventional commit message,
   for example `feat: add freeze control`, `fix: handle busy camera`,
   `docs: clarify OBS workflow`, `ci: add release check`, `test: cover config`.
3. Update the README, `config.example.toml` and `CHANGELOG.md` when behaviour
   or user-facing settings change.
4. Fill in the [pull request template](.github/PULL_REQUEST_TEMPLATE.md) and
   link the relevant issue.

Useful commands for a quick smoke test on real hardware:

```sh
hyprcam --list-devices
hyprcam --settings
hyprcam-toggle
hyprctl clients
```

## Releases

Maintainers tag `v*` releases (for example `v0.1.0`). The Release workflow
builds an sdist and wheel and attaches them to the GitHub Release. Publishing
to PyPI is opt-in via the `ENABLE_PYPI_PUBLISH` repository variable and PyPI
Trusted Publishing; see the Publishing section of the README.
