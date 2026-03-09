# Multi-IDE Launcher

Launch multiple instances of VS Code, Cursor, Codex & Antigravity — each with separate profiles for different accounts.

---

## What it does

Easily launch **VS Code**, **Cursor**, **Antigravity**, and **Codex** with separate user-data per profile. Use different profiles to sign in to different accounts (e.g. multiple GitHub accounts, different marketplace logins) without switching Windows users. Manage profiles per IDE with one click.

---

## Requirements

- **Windows** 10 or 11
- One or more of: **VS Code**, **Cursor**, **Antigravity**, **Codex**
- **Python 3.x** only if you run or build from source

---

## Installation

### Option A — Installer (recommended)

1. Download **MultiIDELauncher-Setup.exe** from [Releases](https://github.com/AdamNatad/MultiIDELauncher/releases).
2. Run the installer (admin required).
3. Install path: `C:\Program Files\MultiIDELauncher\`.
4. Launch from the Start Menu (or Desktop) shortcut.

Config and crash log are created in the install folder on first run.

### Option B — Portable (ZIP)

1. Download **MultiIDELauncher-Portable.zip** from [Releases](https://github.com/AdamNatad/MultiIDELauncher/releases).
2. Extract anywhere (e.g. `D:\Tools\MultiIDELauncher`).
3. Run **MultiIDELauncher.exe**.

Config and crash log are created in the same folder as the EXE.

### Option C — Run from source

```bash
git clone https://github.com/AdamNatad/MultiIDELauncher.git
cd MultiIDELauncher
python src/launcher.py
```

---

## Usage

1. **Tabs** — Switch between VS Code, Cursor, Antigravity, and Codex.
2. **Paths** — Use **Browse** / **Detect** in each tab to set the IDE executable path.
3. **Profiles** — Click **Add** and enter a profile name (folders are created automatically).
4. **Launch** — Select a profile and click **Launch**, or double-click a row.
5. **Save** — Click **Save Config** to write `config.ini` (changes are not auto-saved).

Theme and UI scale apply after you save config and restart the app.

---

## Building from source

Build produces **two outputs** in `output/`: **portable ZIP** and **installer**.

### Prerequisites

- **Python 3.x** and `pip install pyinstaller`
- **Inno Setup 6** — [Download](https://jrsoftware.org/isinfo.php) (e.g. `C:\Program Files (x86)\Inno Setup 6`)
- **Logo** — 512×512 px PNG in `assets/app_icon.png` (optional; run `python build/build_icon.py` to generate `app.ico`)

### One-command build

From the **project root**:

```bash
python build.py
```

**Output:**

| Artifact      | Path |
|---------------|------|
| Portable ZIP  | `output/MultiIDELauncher-Portable.zip` |
| Installer     | `output/MultiIDELauncher-Setup.exe`   |

See **[BUILD.md](BUILD.md)** for step-by-step and folder layout.

---

## Project structure

```
MultiIDELauncher/
├── build.py
├── README.md
├── BUILD.md
├── CHANGELOG.md
├── src/
│   └── launcher.py
├── assets/
│   └── app_icon.png
├── build/
│   ├── build_icon.py
│   └── installer.iss
├── dist/                    (generated)
│   └── MultiIDELauncher.exe
└── output/                  (generated)
    ├── MultiIDELauncher-Portable.zip
    └── MultiIDELauncher-Setup.exe
```

| Path | Purpose |
|------|---------|
| `build.py` | Full build → ZIP + installer |
| `src/launcher.py` | Main app |
| `assets/app_icon.png` | 512×512 logo for `app.ico` |
| `build/build_icon.py` | PNG → app.ico |
| `build/installer.iss` | Inno Setup script |
| `dist/`, `output/` | Build output (generated) |

---

## Changelog

[CHANGELOG.md](CHANGELOG.md) — all notable changes per release.

---

## Support / Help

- **Bugs / issues:** [GitHub Issues](https://github.com/AdamNatad/MultiIDELauncher/issues)

---

## License

[LICENSE](LICENSE) in this repo.

---

**Multi-IDE Launcher** — Launch multiple instances of VS Code, Cursor, Codex & Antigravity.
