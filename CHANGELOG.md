# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-11-23

Publishing and packaging release. Entries below are derived from the commits in
this release.

### Added

- Gated PyPI Trusted Publishing workflow, enabled by the `ENABLE_PYPI_PUBLISH` repository variable (`3982514`); first release published to PyPI.
- Expanded PyPI package metadata: full description, license expression, keywords, classifiers and project URLs (`dc9b574`).
- AUR-ready packaging under `packaging/aur/` (`PKGBUILD`, `.SRCINFO`, submission notes) (`b26fbcf`, `a988fd3`).
- Contributing guide, code of conduct, changelog, issue forms, pull request template and weekly Dependabot updates (`4f5f0dc`, `1da31a8`).
- PyPI and AUR README badges (`e58082b`).

### Changed

- README rewritten with badges, install paths, configuration reference, OBS workflow, FAQ and publishing setup (`9069020`, `c209645`).
- Dependency updates: `softprops/action-gh-release` 2→3, `actions/checkout` 4→7 and `actions/setup-python` 5→7 (`50d7322`, `73490f4`, `8fcdcfc`).
- Package version and installation documentation aligned to the published 0.2.1 release.

## [0.1.0] - 2026-11-23

First tagged release. Entries below are derived from the commits in this release.

### Added

- Repository metadata and MIT license (`4d96d7d`).
- TOML configuration loader, validation, CLI overrides and `hyprcam --list-devices` device discovery (`526f76d`).
- Frameless camera window with live V4L2 capture through OpenCV in a Qt worker thread (`983a848`).
- Settings dialog with live apply and persistence to `config.toml` (`35885ba`).
- Toggle launcher (`hyprcam-toggle`) and Hyprland Lua keybinding/window-rule integration (`78cb357`).
- README, example config and desktop entry (`aa64815`).
- Lint, format, type-check, test and GitHub Release workflows (`609567c`).
- Config, CLI and device discovery tests (`94c531b`).
- Idempotent user-level installer script (`b2f863a`).
- PATH, desktop installation and first-run configuration documentation (`ba58c09`).

### Fixed

- Use the valid `border_size` field in the Lua window rules (`ea89f82`).

[Unreleased]: https://github.com/mhdztr/hyprcam/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/mhdztr/hyprcam/releases/tag/v0.2.1
[0.1.0]: https://github.com/mhdztr/hyprcam/releases/tag/v0.1.0
