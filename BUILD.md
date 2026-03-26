# Build — IDE Launcher (v2.0.1)

Build produces **two artifacts** in `output/`: **portable ZIP** and **installer** (Setup.exe).

---

## Build scripts

All build automation for this repo:

| File | Purpose |
|------|---------|
| [`build.py`](build.py) (project root) | **Main entry.** Clears `output/`, drops legacy PyInstaller folders under `build/`, runs icon step → PyInstaller → portable ZIP → Inno installer. |
| [`build/build_icon.py`](build/build_icon.py) | Converts `assets/app_icon.png` (or a path you pass) to `app.ico` in the project root. Invoked by `build.py` when the PNG exists; can be run alone for icon-only refresh. |
| [`build/installer.iss`](build/installer.iss) | Inno Setup 6 script: packages `dist/IDELauncher.exe`, shortcuts, install path. Compiled by `ISCC.exe` (called from `build.py` step 4). |

There are no other build batch files, spec files, or CI workflows in this repository; `python build.py` is the supported full pipeline.

---

## One-command build

From the **project root**:

```bash
python build.py
```

Steps run in order:

1. **Icon** — Clears `output/`, then `build/build_icon.py` → `app.ico` (from `assets/app_icon.png`).
2. **EXE** — PyInstaller on `src/launcher.py` → `dist/IDELauncher.exe`.
3. **Portable ZIP** → `output/IDELauncher-Portable.zip`.
4. **Installer** — Inno Setup 6 (`build/installer.iss`) → `output/IDELauncher-Setup.exe`.

---

## Prerequisites

- **Python 3.x** and `pip install pyinstaller`
- **Inno Setup 6** — [Download](https://jrsoftware.org/isinfo.php), e.g. `C:\Program Files (x86)\Inno Setup 6`
- **Logo** — 512×512 px PNG at `assets/app_icon.png` (optional; script will warn if missing)

---

## Step-by-step (manual)

**1. Icon**

```bash
python build/build_icon.py
```

Custom logo:

```bash
python build/build_icon.py path/to/logo.png
```

**2. EXE**

```bash
pyinstaller --onefile --noconsole --icon=app.ico --add-data "app.ico;." --name "IDELauncher" src/launcher.py
```

Output: `dist/IDELauncher.exe`.

**3. Portable ZIP**

Create `output/` and zip the EXE (e.g. with PowerShell `Compress-Archive` or 7-Zip).  
`build.py` does this automatically using the standard library.

**4. Installer**

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build/installer.iss
```

Or open `build/installer.iss` in Inno Setup 6 and use **Build → Compile**.

---

## Installer behaviour

- **Install path:** `C:\Program Files\IDELauncher\`
- **Permissions:** Users get write access to the install folder (config and crash log beside the EXE).
- **Shortcuts:** Start Menu; optional Desktop icon.
- **Uninstall:** Windows Add or remove programs.

---

## Folder layout

- **Root:** `build.py` (entry point), `src/launcher.py`, `assets/`, README/BUILD/CHANGELOG.
- **build/** — `build_icon.py`, `installer.iss`.
- **output/** — Cleared at start of build; holds `IDELauncher-Portable.zip` and `IDELauncher-Setup.exe`.
- **dist/** — PyInstaller output (`IDELauncher.exe`); not in git.
