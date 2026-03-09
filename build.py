"""
Multi-IDE Launcher — Full build script (v2.0.0).

Produces:
  output/MultiIDELauncher-Portable.zip
  output/MultiIDELauncher-Setup.exe

Run from project root:  python build.py

Requires: PyInstaller, Inno Setup 6 (for installer).
Optional: assets/app_icon.png for app.ico (skip icon step if missing).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
EXE_PROCESS_NAME = "MultiIDELauncher.exe"
EXE_NAME = "MultiIDELauncher.exe"
OUT_DIR = os.path.join(ROOT, "output")
PORTABLE_ZIP = os.path.join(ROOT, "output", "MultiIDELauncher-Portable.zip")
SETUP_EXE = os.path.join(ROOT, "output", "MultiIDELauncher-Setup.exe")
DIST_EXE = os.path.join(ROOT, "dist", EXE_NAME)
ISCC = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"


def kill_running_process() -> None:
    """Kill MultiIDELauncher if running so the build can overwrite the EXE."""
    if sys.platform != "win32":
        return
    try:
        r = subprocess.run(
            ["taskkill", "/IM", EXE_PROCESS_NAME, "/F"],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        if r.returncode == 0:
            print(f"  Killed running {EXE_PROCESS_NAME}")
    except Exception:
        pass


def run(cmd: list[str], cwd: str | None = None) -> bool:
    cwd = cwd or ROOT
    cmd_str = " ".join(f'"{x}"' if " " in x else x for x in cmd)
    print(f"  $ {cmd_str}")
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        print(f"  Exit code: {r.returncode}")
    return r.returncode == 0


def step_icon() -> bool:
    print("\n[1/4] Building app.ico from assets/app_icon.png ...")
    png = os.path.join(ROOT, "assets", "app_icon.png")
    script = os.path.join(ROOT, "build", "build_icon.py")
    if not os.path.isfile(script):
        print("  ERROR: build/build_icon.py not found.")
        return False
    if not os.path.isfile(png):
        print("  WARNING: assets/app_icon.png not found. Skipping icon (app.ico will be missing).")
        return True
    return run([sys.executable, script], cwd=ROOT)


def _pyinstaller_cmd(ico: str | None) -> list[str]:
    """Use Scripts/pyinstaller.exe when present (avoids -m pyinstaller resolution issues)."""
    python_dir = os.path.dirname(sys.executable)
    scripts = os.path.join(python_dir, "Scripts", "pyinstaller.exe")
    if os.path.isfile(scripts):
        cmd = [scripts]
    else:
        cmd = [sys.executable, "-m", "pyinstaller"]
    if ico:
        cmd.extend(["--icon", ico, "--add-data", f"{ico};."])
    cmd.extend(["--onefile", "--noconsole", "--name", "MultiIDELauncher"])
    return cmd


def step_pyinstaller() -> bool:
    print("\n[2/4] Building EXE with PyInstaller ...")
    launcher = os.path.join(ROOT, "src", "launcher.py")
    ico = os.path.join(ROOT, "app.ico") if os.path.isfile(os.path.join(ROOT, "app.ico")) else None
    if not os.path.isfile(launcher):
        print("  ERROR: src/launcher.py not found.")
        return False
    if not ico:
        print("  (No app.ico; building without icon)")

    cmd = _pyinstaller_cmd(ico)
    cmd.append(launcher)

    ok = run(cmd, cwd=ROOT)
    if not ok:
        print("  If the error is 'No module named pyinstaller', install for this Python:")
        print(f"    {sys.executable} -m pip install pyinstaller")
    return ok


def step_zip() -> bool:
    print("\n[3/4] Creating portable ZIP ...")
    os.makedirs(OUT_DIR, exist_ok=True)
    if not os.path.isfile(DIST_EXE):
        print("  ERROR: dist/ executable not found. Run step 2 first.")
        return False
    try:
        with zipfile.ZipFile(PORTABLE_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(DIST_EXE, EXE_NAME)
        print(f"  -> {PORTABLE_ZIP}")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def step_installer() -> bool:
    print("\n[4/4] Building installer (Inno Setup 6) ...")
    if not os.path.isfile(ISCC):
        print(f"  ERROR: Inno Setup 6 not found at {ISCC}")
        print("  Install from: https://jrsoftware.org/isinfo.php")
        return False
    iss_abs = os.path.join(ROOT, "build", "installer.iss")
    if not os.path.isfile(iss_abs):
        print("  ERROR: build/installer.iss not found.")
        return False
    return run([ISCC, iss_abs], cwd=ROOT)


def clear_output() -> None:
    """Remove output folder so the build starts from a clean state."""
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
        print(f"  Cleared {OUT_DIR}")


def clear_old_build_cache() -> None:
    """Remove legacy PyInstaller cache (VSCodeMD) from project rename."""
    legacy = os.path.join(ROOT, "build", "VSCodeMD")
    if os.path.isdir(legacy):
        shutil.rmtree(legacy)
        print(f"  Cleared legacy cache: build/VSCodeMD")


def main() -> int:
    print("\n=== Multi-IDE Launcher — Full build (portable ZIP + installer) ===")
    kill_running_process()
    clear_output()
    clear_old_build_cache()
    if not step_icon():
        return 1
    if not step_pyinstaller():
        return 1
    if not step_zip():
        return 1
    if not step_installer():
        return 1
    print("\n=== Done ===")
    print(f"\n  Portable ZIP : {PORTABLE_ZIP}")
    print(f"  Installer    : {SETUP_EXE}\n")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception as e:
        print(f"\nERROR: {e}")
        code = 1
    if sys.platform == "win32":
        input("\nPress Enter to close...")
    sys.exit(code)
