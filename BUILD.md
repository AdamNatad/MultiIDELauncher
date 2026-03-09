# Build — Multi-IDE Launcher (v2.0.0)

Build produces **two artifacts** in `output/`: **portable ZIP** and **installer** (Setup.exe).

---

## One-command build

From the **project root**:

```bash
python build.py
```

Steps run in order:

1. **Icon** — Clears `output/`, then `build/build_icon.py` → `app.ico` (from `assets/app_icon.png`).
2. **EXE** — PyInstaller on `src/launcher.py` → `dist/MultiIDELauncher.exe`.
3. **Portable ZIP** → `output/MultiIDELauncher-Portable.zip`.
4. **Installer** — Inno Setup 6 (`build/installer.iss`) → `output/MultiIDELauncher-Setup.exe`.

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
pyinstaller --onefile --noconsole --icon=app.ico --add-data "app.ico;." --name "MultiIDELauncher" src/launcher.py
```

Output: `dist/MultiIDELauncher.exe`.

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

- **Install path:** `C:\Program Files\MultiIDELauncher\`
- **Permissions:** Users get write access to the install folder (config and crash log beside the EXE).
- **Shortcuts:** Start Menu; optional Desktop icon.
- **Uninstall:** Windows Add or remove programs.

---

## Folder layout

- **Root:** `build.py` (entry point), `src/launcher.py`, `assets/`, README/BUILD/CHANGELOG.
- **build/** — `build_icon.py`, `installer.iss`.
- **output/** — Cleared at start of build; holds `MultiIDELauncher-Portable.zip` and `MultiIDELauncher-Setup.exe`.
- **dist/** — PyInstaller output (`MultiIDELauncher.exe`); not in git.
