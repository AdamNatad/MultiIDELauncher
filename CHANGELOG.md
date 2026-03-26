# Changelog

Notable changes. Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.1] — 2026-03-26

### Changed

- Display name and window title: **IDE Launcher by Adam Natad**.
- Executable, portable ZIP, and installer: `IDELauncher.exe`, `IDELauncher-Portable.zip`, `IDELauncher-Setup.exe`.
- Default profile directory: `%LOCALAPPDATA%\IDELauncher\Profiles`.

---

## [2.0.0] — 2026-03-10

Major revamp: Multi-IDE Launcher.

### Added

- Support for **VS Code**, **Cursor**, **Antigravity**, and **Codex** with separate tabs.
- Auto-detection of all four IDEs on Windows (including Codex in WindowsApps).
- Simplified profile creation: name only; paths derived automatically from base dir.
- Codex launch via `CODEX_HOME` environment variable.
- Debounced window resize to fix lag/stutter.

### Changed

- Rebranded to **Multi-IDE Launcher**.
- Tabbed UI: one tab per IDE with its own profile list and path settings.
- Config schema: new `[paths]` section; profiles use `ide|name` format.
- Default base dir: `%LOCALAPPDATA%\MultiIDELauncher\Profiles`.
- EXE and installer: `MultiIDELauncher.exe`, `MultiIDELauncher-Setup.exe`.

### Migration

- Old config (vscode_path, profiles without `ide|` prefix) is migrated automatically on load.

---

## [1.0.0] — 2026-03-01

First release.

### Added

- Windows launcher for multiple VS Code instances; each profile has its own user-data and extensions folders.
- Profile management: add, edit, delete; launch via button or double-click; optional new-window and extra CLI args.
- Dark / Light theme and UI scale (Auto, 100%–300%); scale applies after save + relaunch.
- Config and crash log next to the EXE (no AppData); save is explicit (no auto-save).
- Themed modals for remove profile, save config, UI scale, and report bugs; Copy Url in report-bugs dialog; footer “Report Bugs?” (red on hover).
- Min window size 1024×620; right rail always visible.
- App icon (PNG → app.ico); all windows use it.
- Build: `python build.py` → portable ZIP and Inno Setup installer. Install path: `C:\Program Files\MultiIDELauncher\`; Users get write so config/crash work. Support/Help: GitHub repo.
- Global excepthook: uncaught errors go to crash.log and open report-bugs modal when possible.

### Fixed

- ConfigParser crash when `ui_scale` contained `%` (interpolation disabled).
- Combobox text turning white on Light theme when focused (state mappings for TCombobox).

---

[2.0.1]: https://github.com/AdamNatad/IDELauncher/releases/tag/v2.0.1
[2.0.0]: https://github.com/AdamNatad/IDELauncher/releases/tag/v2.0.0
[1.0.0]: https://github.com/AdamNatad/IDELauncher/releases/tag/v1.0.0
