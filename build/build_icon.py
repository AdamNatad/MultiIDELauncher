"""Build app.ico from your logo PNG for Windows (PyInstaller + Inno Setup).

Run from project root:  python build\\build_icon.py
Or with custom logo:     python build\\build_icon.py path\\to\\logo.png

Logo specs (e.g. from Canva): 512x512 px (or 256x256), PNG, square.
Output: app.ico in project root (used by PyInstaller and installer.iss).
"""
import os
import struct
import sys

# Project root = parent of build/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_PNG = os.path.join(ROOT, "assets", "app_icon.png")
ICO_PATH = os.path.join(ROOT, "app.ico")


def main():
    png_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PNG
    png_path = os.path.normpath(os.path.abspath(png_path))

    if not os.path.isfile(png_path):
        assets_dir = os.path.join(ROOT, "assets")
        if not os.path.isdir(assets_dir):
            os.makedirs(assets_dir)
            print(f"Created folder: {assets_dir}")
        print(f"Missing logo: {png_path}")
        print("  Add your 512x512 (or 256x256) PNG as assets\\app_icon.png")
        print("  Or run: python build\\build_icon.py path\\to\\your\\logo.png")
        return 1

    with open(png_path, "rb") as f:
        png_data = f.read()

    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png_data), 6 + 16)

    with open(ICO_PATH, "wb") as f:
        f.write(header)
        f.write(entry)
        f.write(png_data)

    png_kb = len(png_data) / 1024
    ico_kb = (6 + 16 + len(png_data)) / 1024
    print(f"Created: {ICO_PATH} ({ico_kb:.1f} KB from {png_kb:.1f} KB PNG)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
