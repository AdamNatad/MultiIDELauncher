# IDE Launcher
# Launch multiple instances of VSCode, Cursor, Codex, Antigravity & Claude
# Build from project root: python build.py

from __future__ import annotations

import glob
import os
import re
import sys
import shutil
import platform
import subprocess
import ctypes
import configparser
import traceback
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont

APP_NAME = "IDE Launcher by Adam Natad"
APP_TAGLINE = "Launch multiple instances of VSCode, Cursor, Codex, Antigravity & Claude"
CONFIG_FILENAME = "config.ini"
REPORT_BUGS_URL = "https://github.com/AdamNatad/IDELauncher/issues"

IDE_TYPES = ("vscode", "cursor", "antigravity", "codex", "claude")
IDE_DISPLAY_NAMES = {"vscode": "VSCode", "cursor": "Cursor", "antigravity": "Antigravity", "codex": "Codex", "claude": "Claude"}

_app_ref: "App | None" = None  # used by excepthook


# --- Helpers ---

def os_name() -> str:
    return platform.system()

def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def config_path() -> str:
    return os.path.join(app_dir(), CONFIG_FILENAME)


def app_icon_path() -> str:
    """app.ico path (dev or frozen)."""
    return os.path.join(getattr(sys, "_MEIPASS", app_dir()), "app.ico")

def crash_log_path() -> str:
    return os.path.join(app_dir(), "crash.log")

def norm(p: str) -> str:
    return os.path.normpath(os.path.expandvars(os.path.expanduser((p or "").strip())))

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_windows_dpi() -> int:
    """Windows logical DPI for UI scale Auto; 96 when not Windows."""
    if platform.system() != "Windows":
        return 96
    try:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        hdc = user32.GetDC(0)
        if not hdc:
            return 96
        dpi = gdi32.GetDeviceCaps(hdc, 88)
        user32.ReleaseDC(0, hdc)
        return int(dpi) if dpi and int(dpi) > 0 else 96
    except Exception:
        return 96


def open_folder_cross_platform(path: str) -> None:
    path = norm(path)
    ensure_dir(path)
    if os_name() == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif os_name() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

def split_args(extra: str) -> list[str]:
    extra = (extra or "").strip()
    if not extra:
        return []
    try:
        import shlex
        return shlex.split(extra, posix=(os_name() != "Windows"))
    except Exception:
        return extra.split()


# --- IDE detection ---

def _dedupe_paths(cands: list[str]) -> list[str]:
    out, seen = [], set()
    for p in cands:
        if not p:
            continue
        p = norm(p)
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def ide_candidates(ide: str) -> list[str]:
    cands: list[str] = []
    local = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

    if os_name() == "Windows":
        if ide == "vscode":
            cands += [
                os.path.join(program_files, r"Microsoft VS Code\Code.exe"),
                os.path.join(program_files_x86, r"Microsoft VS Code\Code.exe"),
            ]
            if local:
                cands += [
                    os.path.join(local, r"Programs\Microsoft VS Code\Code.exe"),
                    os.path.join(local, r"Programs\Microsoft VS Code Insiders\Code - Insiders.exe"),
                ]
            which_code = shutil.which("code.cmd") or shutil.which("code.exe") or shutil.which("code")
            if which_code:
                cands.append(which_code)
        elif ide == "cursor":
            cands.append(os.path.join(program_files, r"cursor\Cursor.exe"))
            if local:
                cands.append(os.path.join(local, r"Programs\cursor\Cursor.exe"))
            which_cursor = shutil.which("Cursor.exe") or shutil.which("cursor")
            if which_cursor:
                cands.append(which_cursor)
        elif ide == "antigravity":
            if local:
                cands.append(os.path.join(local, r"Programs\Antigravity\Antigravity.exe"))
            which_agy = shutil.which("Antigravity.exe") or shutil.which("agy")
            if which_agy:
                cands.append(which_agy)
        elif ide == "codex":
            winapps = os.path.join(program_files, "WindowsApps")
            if os.path.isdir(winapps):
                pattern = os.path.join(winapps, "OpenAI.Codex_*")
                for match in glob.glob(pattern):
                    exe = os.path.join(match, "app", "Codex.exe")
                    if os.path.isfile(exe):
                        cands.append(exe)
        elif ide == "claude":
            winapps = os.path.join(program_files, "WindowsApps")
            if os.path.isdir(winapps):
                pattern = os.path.join(winapps, "Claude_*")
                for match in glob.glob(pattern):
                    exe = os.path.join(match, "app", "claude.exe")
                    if os.path.isfile(exe):
                        cands.append(exe)
    elif os_name() == "Darwin":
        if ide == "vscode":
            cands += [
                "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
                "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code",
                os.path.expanduser("~/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"),
            ]
            which_code = shutil.which("code")
            if which_code:
                cands.insert(0, which_code)
        elif ide == "cursor":
            cands.append("/Applications/Cursor.app/Contents/MacOS/Cursor")
            which_cursor = shutil.which("cursor")
            if which_cursor:
                cands.insert(0, which_cursor)
        elif ide == "antigravity":
            cands.append("/Applications/Antigravity.app/Contents/MacOS/Antigravity")
        elif ide == "codex":
            cands.append("/Applications/Codex.app/Contents/MacOS/Codex")
        elif ide == "claude":
            cands.append("/Applications/Claude Code.app/Contents/MacOS/claude")
    else:
        if ide == "vscode":
            cands += ["/usr/bin/code", "/usr/local/bin/code", "/snap/bin/code"]
            which_code = shutil.which("code")
            if which_code:
                cands.insert(0, which_code)
        elif ide == "cursor":
            cands.append("/usr/bin/cursor")
            which_cursor = shutil.which("cursor")
            if which_cursor:
                cands.insert(0, which_cursor)
        elif ide == "antigravity":
            cands.append("/usr/bin/antigravity")
        elif ide == "codex":
            cands.append("/usr/bin/codex")
        elif ide == "claude":
            cands.append("/usr/bin/claude")

    return _dedupe_paths(cands)


def autodetect_ide_path(ide: str) -> str:
    for p in ide_candidates(ide):
        if os.path.isfile(p) or shutil.which(p):
            return resolve_ide_exe(p, ide)  # Always return actual .exe, not bin/cursor etc.
    return ""


def is_executable_path(p: str) -> bool:
    p = norm(p)
    return bool(p) and (os.path.isfile(p) or shutil.which(p))


def resolve_ide_exe(path: str, ide: str) -> str:
    """Resolve script/launcher paths to actual .exe on Windows (fixes WinError 193)."""
    path = norm(path)
    if not path:
        return path
    if os_name() != "Windows":
        return path
    # Already a proper .exe
    if path.lower().endswith(".exe") and os.path.isfile(path):
        return path
    # Path points to bin/cursor, bin/code, etc. — resolve to parent Cursor.exe, Code.exe
    path_lower = path.lower().replace("/", "\\")
    exe_name = None
    if ide == "cursor" and ("cursor" in path_lower or "bin" in path_lower):
        exe_name = "Cursor.exe"
    elif ide == "vscode" and ("code" in path_lower or "bin" in path_lower):
        exe_name = "Code.exe"
    elif ide == "antigravity" and ("antigravity" in path_lower or "bin" in path_lower):
        exe_name = "Antigravity.exe"
    elif ide == "claude" and ("claude" in path_lower or "bin" in path_lower):
        exe_name = "claude.exe"
    if exe_name:
        # Walk up from path to find install root (e.g. .../cursor/ or .../Microsoft VS Code/)
        dir_ = os.path.dirname(path) if os.path.isfile(path) else path
        for _ in range(8):  # limit depth
            if not dir_ or dir_ == os.path.dirname(dir_):
                break
            candidate = os.path.join(dir_, exe_name)
            if os.path.isfile(candidate):
                return candidate
            dir_ = os.path.dirname(dir_)
    return path


# --- Config + model ---

class Profile:
    """Profile for VS Code, Cursor, or Antigravity (user_data + extensions) or Codex (codex_home only)."""

    def __init__(self, ide: str, name: str, user_data: str = "", extensions: str = "", codex_home: str = ""):
        self.ide = ide
        self.name = name
        self.user_data = user_data
        self.extensions = extensions
        self.codex_home = codex_home

    def ensure_folders(self) -> None:
        if self.ide == "codex":
            ensure_dir(self.codex_home)
        else:
            ensure_dir(self.user_data)
            ensure_dir(self.extensions)

    def folder_path(self) -> str:
        """Path to open in explorer (user_data or codex_home)."""
        return self.codex_home if self.ide == "codex" else self.user_data


def make_profile_from_name(ide: str, name: str, base_dir: str) -> Profile:
    """Create a Profile with paths derived from base_dir + ide + sanitized name."""
    base_dir = norm(base_dir)
    safe = _sanitize_profile_name(name) or "profile"
    ide_folder = IDE_DISPLAY_NAMES.get(ide, ide).replace(" ", "")
    profile_base = os.path.join(base_dir, ide_folder, safe)
    if ide == "codex":
        return Profile(ide, name, codex_home=profile_base)
    return Profile(
        ide, name,
        user_data=os.path.join(profile_base, "user-data"),
        extensions=os.path.join(profile_base, "extensions"),
    )


def _sanitize_profile_name(name: str) -> str:
    """Sanitize for use in path (remove invalid chars)."""
    return re.sub(r'[<>:"/\\|?*]', "_", (name or "").strip())


class ConfigManager:
    def __init__(self, path: str):
        self.path = path
        self.cfg = configparser.ConfigParser(interpolation=None)

    def _default_base_dir(self) -> str:
        if os_name() == "Windows":
            local = os.environ.get("LOCALAPPDATA", "")
            if local:
                return os.path.join(local, "IDELauncher", "Profiles")
            return r"D:\MultiIDE-Profiles"
        return os.path.expanduser("~/IDELauncher/Profiles")

    def _migrate_old_config(self) -> None:
        """Migrate old vscode_path + profiles format to new paths + ide|name format."""
        app = self.cfg["app"]
        profiles = self.cfg["profiles"]
        # Migrate old default base_dir to AppData
        old_defaults = (norm(r"D:\VSCode-UData"), norm(r"D:\MultiIDE-Profiles"))
        current_base = norm(app.get("base_dir", ""))
        if current_base in old_defaults:
            app["base_dir"] = self._default_base_dir()
        old_vscode = app.get("vscode_path", "")
        if old_vscode:
            if "paths" not in self.cfg:
                self.cfg["paths"] = {}
            self.cfg["paths"]["vscode"] = old_vscode
            if "vscode_path" in app:
                del app["vscode_path"]
        migrated = False
        new_profiles = {}
        for key, value in list(profiles.items()):
            if "|" not in key and not key.startswith(("vscode|", "cursor|", "antigravity|", "codex|", "claude|")):
                new_profiles[f"vscode|{key}"] = value
                migrated = True
            else:
                new_profiles[key] = value
        if migrated or old_vscode:
            self.cfg["profiles"] = new_profiles
            self.save()

    def load(self) -> None:
        if os.path.isfile(self.path):
            self.cfg.read(self.path, encoding="utf-8")
        else:
            self._create_default()

        if "app" not in self.cfg:
            self.cfg["app"] = {}
        if "paths" not in self.cfg:
            self.cfg["paths"] = {}
        if "profiles" not in self.cfg:
            self.cfg["profiles"] = {}

        self._migrate_old_config()

        app = self.cfg["app"]
        paths = self.cfg["paths"]
        app.setdefault("base_dir", self._default_base_dir())
        app.setdefault("open_new_window", "1")
        app.setdefault("reuse_existing_window", "0")
        app.setdefault("extra_args", "")
        app.setdefault("theme", "Dark")
        app.setdefault("ui_scale", "Auto")

        for ide in IDE_TYPES:
            paths.setdefault(ide, autodetect_ide_path(ide))

        self._normalize_ide_paths()
        self._deduplicate_profiles()

        self.sync_profiles_to_disk()

        if "ui_scale" not in app:
            app["ui_scale"] = "Auto"
            self.save()

    def _create_default(self) -> None:
        self.cfg["app"] = {
            "base_dir": self._default_base_dir(),
            "open_new_window": "1",
            "reuse_existing_window": "0",
            "extra_args": "",
            "theme": "Dark",
            "ui_scale": "Auto",
        }
        self.cfg["paths"] = {ide: autodetect_ide_path(ide) for ide in IDE_TYPES}
        self.cfg["profiles"] = {}
        ensure_dir(app_dir())
        self.save()

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            self.cfg.write(f)

    def get_app(self) -> dict:
        return dict(self.cfg["app"])

    def set_app(self, key: str, value: str) -> None:
        self.cfg["app"][key] = value

    def get_path(self, ide: str) -> str:
        return norm(self.cfg["paths"].get(ide, ""))

    def set_path(self, ide: str, value: str) -> None:
        self.cfg["paths"][ide] = value

    def get_profiles_for_ide(self, ide: str) -> list[Profile]:
        out: list[Profile] = []
        base_dir = norm(self.cfg["app"].get("base_dir", ""))
        ide_folder = IDE_DISPLAY_NAMES.get(ide, ide).replace(" ", "")
        parent_dir = os.path.join(base_dir, ide_folder) if base_dir else ""
        disk_names: dict[str, str] = {}
        if parent_dir and os.path.isdir(parent_dir):
            try:
                for entry in os.listdir(parent_dir):
                    if os.path.isdir(os.path.join(parent_dir, entry)):
                        disk_names[entry.lower()] = entry
            except OSError:
                pass
        prefix = f"{ide}|"
        for key, value in self.cfg["profiles"].items():
            if not key.startswith(prefix):
                continue
            name = key[len(prefix) :]
            if disk_names and name.lower() in disk_names:
                name = disk_names[name.lower()]
            if ide == "codex":
                out.append(Profile(ide, name, codex_home=norm(value)))
            else:
                parts = value.split("|", 1)
                ud = norm(parts[0]) if parts else ""
                ex = norm(parts[1]) if len(parts) > 1 else ""
                out.append(Profile(ide, name, ud, ex))
        out.sort(key=lambda p: p.name.lower())
        return out

    def upsert_profile(self, p: Profile) -> None:
        key = f"{p.ide}|{p.name}"
        if p.ide == "codex":
            self.cfg["profiles"][key] = p.codex_home
        else:
            self.cfg["profiles"][key] = f"{p.user_data}|{p.extensions}"

    def delete_profile(self, ide: str, name: str) -> None:
        """Delete profile by name (case-insensitive lookup)."""
        key = self._find_profile_key(ide, name)
        if key:
            del self.cfg["profiles"][key]

    def _normalize_ide_paths(self) -> None:
        """Fix stored paths: resolve bin/cursor etc. to actual .exe; replace invalid paths via autodetect."""
        paths = self.cfg["paths"]
        changed = False
        for ide in IDE_TYPES:
            p = paths.get(ide, "")
            resolved = resolve_ide_exe(norm(p), ide) if p else ""
            if resolved and os.path.isfile(resolved):
                if resolved != norm(p):
                    paths[ide] = resolved
                    changed = True
            else:
                detected = autodetect_ide_path(ide)
                if detected and detected != paths.get(ide, ""):
                    paths[ide] = detected
                    changed = True
        if changed:
            self.save()

    def recheck_all_paths(self) -> bool:
        """Run autodetect for all IDEs and update config. Returns True if any path changed."""
        paths = self.cfg["paths"]
        changed = False
        for ide in IDE_TYPES:
            detected = autodetect_ide_path(ide)
            current = norm(paths.get(ide, ""))
            new_val = detected if detected else current
            if new_val != current:
                paths[ide] = new_val
                changed = True
        if changed:
            self.save()
        return changed

    def _scan_profiles_on_disk(self, base_dir: str) -> list[Profile]:
        """Scan base_dir for existing profile folders and return Profile objects."""
        base_dir = norm(base_dir)
        if not os.path.isdir(base_dir):
            return []
        discovered: list[Profile] = []
        for ide in IDE_TYPES:
            ide_folder = IDE_DISPLAY_NAMES.get(ide, ide).replace(" ", "")
            ide_path = os.path.join(base_dir, ide_folder)
            if not os.path.isdir(ide_path):
                continue
            try:
                for name in os.listdir(ide_path):
                    if name.startswith(".") or name == "__pycache__":
                        continue
                    profile_path = os.path.join(ide_path, name)
                    if not os.path.isdir(profile_path):
                        continue
                    if ide == "codex":
                        discovered.append(Profile(ide, name, codex_home=profile_path))
                    else:
                        ud = os.path.join(profile_path, "user-data")
                        ex = os.path.join(profile_path, "extensions")
                        if os.path.isdir(ud) and os.path.isdir(ex):
                            discovered.append(Profile(ide, name, ud, ex))
            except OSError:
                continue
        return discovered

    def _deduplicate_profiles(self) -> None:
        """Remove duplicate profiles (same ide+name, case-insensitive). Keeps first occurrence."""
        profiles = self.cfg["profiles"]
        seen: dict[str, set[str]] = {ide: set() for ide in IDE_TYPES}
        to_remove = []
        for key in list(profiles.keys()):
            if "|" not in key:
                continue
            ide, name = key.split("|", 1)
            if ide not in seen:
                continue
            name_lower = name.lower()
            if name_lower in seen[ide]:
                to_remove.append(key)
            else:
                seen[ide].add(name_lower)
        for key in to_remove:
            del profiles[key]
        if to_remove:
            self.save()

    def _existing_profile_names_lower(self, ide: str) -> set[str]:
        """Return set of profile names (lowercase) for an IDE."""
        return {p.name.lower() for p in self.get_profiles_for_ide(ide)}

    def _find_profile_key(self, ide: str, name: str) -> str | None:
        """Find config key for profile by case-insensitive name. Used for delete and merge."""
        name_lower = name.lower()
        prefix = f"{ide}|"
        for key in self.cfg["profiles"]:
            if not key.startswith(prefix):
                continue
            if key[len(prefix) :].lower() == name_lower:
                return key
        return None

    def _remove_profiles_not_on_disk(self) -> bool:
        """Remove config profiles whose folders no longer exist on disk."""
        removed = []
        for key in list(self.cfg["profiles"].keys()):
            if "|" not in key:
                continue
            ide, name = key.split("|", 1)
            value = self.cfg["profiles"][key]
            if ide == "codex":
                folder = norm(value)
            else:
                parts = value.split("|", 1)
                ud = norm(parts[0]) if parts else ""
                folder = os.path.dirname(ud) if ud else ""
            if folder and not os.path.isdir(folder):
                del self.cfg["profiles"][key]
                removed.append(key)
        if removed:
            self.save()
        return bool(removed)

    def _merge_scanned_profiles(self) -> bool:
        """Add profiles from disk; sync config to disk casing when profile exists (case-insensitive)."""
        base_dir = norm(self.cfg["app"].get("base_dir", ""))
        if not base_dir:
            return False
        changed = False
        for p in self._scan_profiles_on_disk(base_dir):
            existing_lower = self._existing_profile_names_lower(p.ide)
            if p.name.lower() not in existing_lower:
                self.upsert_profile(p)
                changed = True
            else:
                # Profile exists case-insensitively; sync config to disk casing
                old_key = self._find_profile_key(p.ide, p.name)
                if old_key and old_key != f"{p.ide}|{p.name}":
                    value = self.cfg["profiles"].pop(old_key)
                    self.cfg["profiles"][f"{p.ide}|{p.name}"] = value
                    changed = True
        if changed:
            self.save()
        return changed

    def sync_profiles_to_disk(self) -> bool:
        """Remove profiles not on disk, add new from disk, sync casing. Returns True if config changed."""
        changed = self._remove_profiles_not_on_disk()
        if self._merge_scanned_profiles():
            changed = True
        return changed


# --- Simple dialogs ---

def _center_on(master: tk.Misc, win: tk.Toplevel) -> None:
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    mx = master.winfo_x()
    my = master.winfo_y()
    mw = master.winfo_width()
    mh = master.winfo_height()
    x = mx + max(0, (mw - w) // 2)
    y = my + max(0, (mh - h) // 2)
    win.geometry(f"+{x}+{y}")


class AddProfileDialog(tk.Toplevel):
    """Simple dialog: profile name only. Paths are derived from base_dir + ide + name."""

    def __init__(self, master: "App", ide: str, initial_name: str = ""):
        super().__init__(master)
        self.withdraw()
        self.title(f"Add {IDE_DISPLAY_NAMES.get(ide, ide)} Profile")
        self.resizable(False, False)
        _icon = app_icon_path()
        if os.path.isfile(_icon):
            try:
                self.iconbitmap(_icon)
            except Exception:
                pass
        self.result: str | None = None
        self._master_app = getattr(master, "palette", None) and master or None
        self.var_name = tk.StringVar(value=initial_name or "Profile1")

        if self._master_app:
            self.configure(bg=self._master_app.palette["bg"])
        frm = ttk.Frame(self, style="Card.TFrame" if self._master_app else "TFrame", padding=16)
        frm.grid(row=0, column=0, sticky="nsew")
        frm.columnconfigure(1, weight=1)

        lbl_style = "Card.TLabel" if self._master_app else "TLabel"
        ttk.Label(frm, text="Profile name", style=lbl_style).grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_name, width=36).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=1, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy, takefocus=False, cursor="hand2").pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Create", style="Accent.TButton", command=self._save, takefocus=False, cursor="hand2").pack(side="left")

        self.bind("<Return>", lambda _e: self._save())
        self.bind("<Escape>", lambda _e: self.destroy())

        self.transient(master)
        self.grab_set()
        self.deiconify()
        self.wait_visibility()
        _center_on(master, self)
        self.focus_force()

    def _save(self) -> None:
        name = self.var_name.get().strip()
        if not name:
            d = InfoDialog(self.master, APP_NAME, "Profile name cannot be empty.")
            self.wait_window(d)
            return
        self.result = name
        self.destroy()


class EditProfileDialog(tk.Toplevel):
    """Simple dialog: rename only."""

    def __init__(self, master: "App", ide: str, initial_name: str):
        super().__init__(master)
        self.withdraw()
        self.title(f"Edit {IDE_DISPLAY_NAMES.get(ide, ide)} Profile")
        self.resizable(False, False)
        _icon = app_icon_path()
        if os.path.isfile(_icon):
            try:
                self.iconbitmap(_icon)
            except Exception:
                pass
        self.result: str | None = None
        self._master_app = getattr(master, "palette", None) and master or None
        self.var_name = tk.StringVar(value=initial_name)

        if self._master_app:
            self.configure(bg=self._master_app.palette["bg"])
        frm = ttk.Frame(self, style="Card.TFrame" if self._master_app else "TFrame", padding=16)
        frm.grid(row=0, column=0, sticky="nsew")
        frm.columnconfigure(1, weight=1)

        lbl_style = "Card.TLabel" if self._master_app else "TLabel"
        ttk.Label(frm, text="Profile name", style=lbl_style).grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_name, width=36).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=1, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy, takefocus=False, cursor="hand2").pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Save", style="Accent.TButton", command=self._save, takefocus=False, cursor="hand2").pack(side="left")

        self.bind("<Return>", lambda _e: self._save())
        self.bind("<Escape>", lambda _e: self.destroy())

        self.transient(master)
        self.grab_set()
        self.deiconify()
        self.wait_visibility()
        _center_on(master, self)
        self.focus_force()

    def _save(self) -> None:
        name = self.var_name.get().strip()
        if not name:
            d = InfoDialog(self.master, APP_NAME, "Profile name cannot be empty.")
            self.wait_window(d)
            return
        self.result = name
        self.destroy()


# --- Delete confirm ---

class DeleteConfirmDialog(tk.Toplevel):

    def __init__(self, master: "App", profile_name: str, profile: "Profile"):
        super().__init__(master)
        self.withdraw()
        self.master_app = master
        self.profile_name = profile_name
        self.profile = profile
        self.confirmed = False
        self.delete_from_disk = False

        self.title("Remove profile")
        self.resizable(False, False)
        _icon = app_icon_path()
        if os.path.isfile(_icon):
            try:
                self.iconbitmap(_icon)
            except Exception:
                pass
        self.configure(bg=master.palette["bg"])

        outer = ttk.Frame(self, style="Card.TFrame", padding=16)
        outer.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        ttk.Label(
            outer,
            text=f'"{profile_name}" will be removed from the list.',
            style="Card.TLabel",
            font=(master.base_font.cget("family"), master.base_font.cget("size") + 1, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        ttk.Label(
            outer,
            text="Your data folders stay on disk unless you check the option below.",
            style="Card.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

        ttk.Separator(outer, orient="horizontal").grid(row=2, column=0, sticky="ew", pady=(0, 12))

        self.var_delete_disk = tk.IntVar(value=0)
        cb = ttk.Checkbutton(
            outer,
            text="Delete folder and files on disk",
            variable=self.var_delete_disk,
            style="Danger.TCheckbutton",
            takefocus=False,
            cursor="hand2",
        )
        cb.grid(row=3, column=0, sticky="w", pady=(0, 16))

        btn_row = ttk.Frame(outer)
        btn_row.grid(row=4, column=0, sticky="e")
        ttk.Button(btn_row, text="Cancel", command=self._cancel, takefocus=False, cursor="hand2").pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Remove", style="Danger.TButton", command=self._remove, takefocus=False, cursor="hand2").pack(side="left")

        self.transient(master)
        self.bind("<Escape>", lambda _e: self._cancel())
        self.grab_set()
        self.deiconify()
        self.wait_visibility()
        _center_on(master, self)
        self.focus_force()

    def _cancel(self) -> None:
        self.destroy()

    def _remove(self) -> None:
        self.confirmed = True
        self.delete_from_disk = bool(self.var_delete_disk.get())
        self.destroy()


# --- Save confirm ---

class SaveConfirmDialog(tk.Toplevel):

    def __init__(self, master: "App"):
        super().__init__(master)
        self.withdraw()
        self.confirmed = False

        self.title("Save configuration")
        self.resizable(False, False)
        _icon = app_icon_path()
        if os.path.isfile(_icon):
            try:
                self.iconbitmap(_icon)
            except Exception:
                pass
        self.configure(bg=master.palette["bg"])

        outer = ttk.Frame(self, style="Card.TFrame", padding=16)
        outer.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ttk.Label(
            outer,
            text="Save configuration to file?",
            style="Card.TLabel",
            font=(master.base_font.cget("family"), master.base_font.cget("size") + 1, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        ttk.Label(
            outer,
            text="Your current settings will be written to the config file.",
            style="Card.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        btn_row = ttk.Frame(outer)
        btn_row.grid(row=2, column=0, sticky="e")
        ttk.Button(btn_row, text="Cancel", command=self._cancel, takefocus=False, cursor="hand2").pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Save", style="Accent.TButton", command=self._save, takefocus=False, cursor="hand2").pack(side="left")

        self.transient(master)
        self.bind("<Escape>", lambda _e: self._cancel())
        self.grab_set()
        self.deiconify()
        self.wait_visibility()
        _center_on(master, self)
        self.focus_force()

    def _cancel(self) -> None:
        self.destroy()

    def _save(self) -> None:
        self.confirmed = True
        self.destroy()


# --- Report bugs ---

class ReportBugsDialog(tk.Toplevel):

    def __init__(self, master: "App", error_message: str | None = None):
        super().__init__(master)
        self.withdraw()
        self.title("Report Bugs?")
        self.resizable(False, False)
        _icon = app_icon_path()
        if os.path.isfile(_icon):
            try:
                self.iconbitmap(_icon)
            except Exception:
                pass
        self.configure(bg=master.palette["bg"])

        outer = ttk.Frame(self, style="Card.TFrame", padding=16)
        outer.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        if error_message:
            text = f"An unexpected error occurred.\n\n{error_message}\n\nPlease report it at:\n{REPORT_BUGS_URL}"
        else:
            text = f"Report bugs or post issues at:\n\n{REPORT_BUGS_URL}"
        ttk.Label(outer, text=text, style="Card.TLabel", wraplength=360).grid(row=0, column=0, sticky="w", pady=(0, 16))
        btn_row = ttk.Frame(outer)
        btn_row.grid(row=1, column=0, sticky="e")
        ttk.Button(btn_row, text="Copy Url", style="Accent.TButton", command=self._copy_url, takefocus=False, cursor="hand2").pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="OK", command=self.destroy, takefocus=False, cursor="hand2").pack(side="left")

        self.transient(master)
        self.bind("<Return>", lambda _e: self.destroy())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.grab_set()
        self.deiconify()
        self.wait_visibility()
        _center_on(master, self)
        self.focus_force()

    def _copy_url(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(REPORT_BUGS_URL)
        self.update()


# --- Save and relaunch (UI scale) ---

class SaveAndRelaunchConfirmDialog(tk.Toplevel):

    def __init__(self, master: "App"):
        super().__init__(master)
        self.withdraw()
        self.confirmed = False

        self.title("Save and Relaunch?")
        self.resizable(False, False)
        _icon = app_icon_path()
        if os.path.isfile(_icon):
            try:
                self.iconbitmap(_icon)
            except Exception:
                pass
        self.configure(bg=master.palette["bg"])

        outer = ttk.Frame(self, style="Card.TFrame", padding=16)
        outer.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ttk.Label(
            outer,
            text="Save config and relaunch the app to apply the new UI scale?",
            style="Card.TLabel",
            wraplength=360,
        ).grid(row=0, column=0, sticky="w", pady=(0, 16))

        btn_row = ttk.Frame(outer)
        btn_row.grid(row=1, column=0, sticky="e")
        ttk.Button(btn_row, text="No", command=self._no, takefocus=False, cursor="hand2").pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Yes", style="Accent.TButton", command=self._yes, takefocus=False, cursor="hand2").pack(side="left")

        self.transient(master)
        self.bind("<Escape>", lambda _e: self._no())
        self.bind("<Return>", lambda _e: self._yes())
        self.grab_set()
        self.deiconify()
        self.wait_visibility()
        _center_on(master, self)
        self.focus_force()

    def _no(self) -> None:
        self.destroy()

    def _yes(self) -> None:
        self.confirmed = True
        self.destroy()


# --- Info dialog ---

class InfoDialog(tk.Toplevel):

    def __init__(self, master: "App", title: str, message: str):
        super().__init__(master)
        self.withdraw()
        self.title(title)
        self.resizable(False, False)
        _icon = app_icon_path()
        if os.path.isfile(_icon):
            try:
                self.iconbitmap(_icon)
            except Exception:
                pass
        self.configure(bg=master.palette["bg"])

        outer = ttk.Frame(self, style="Card.TFrame", padding=16)
        outer.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ttk.Label(outer, text=message, style="Card.TLabel", wraplength=360).grid(row=0, column=0, sticky="w", pady=(0, 16))
        ttk.Button(outer, text="OK", style="Accent.TButton", command=self.destroy, takefocus=False, cursor="hand2").grid(row=1, column=0, sticky="e")

        self.transient(master)
        self.bind("<Return>", lambda _e: self.destroy())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.grab_set()
        self.deiconify()
        self.wait_visibility()
        _center_on(master, self)
        self.focus_force()


# --- Main app ---

class App(tk.Tk):
    THEME_OPTIONS = ["Dark", "Light"]
    SCALE_OPTIONS = ["Auto", "100%", "125%", "150%", "175%", "200%", "225%", "250%", "300%"]
    WIDTH = 800
    HEIGHT = 565

    @staticmethod
    def _normalize_theme(raw: str) -> str:
        v = (raw or "").strip().lower()
        return "Dark" if v == "dark" else "Light"

    def _theme_is_dark(self) -> bool:
        return (self.var_theme.get() or "").strip().lower() == "dark"

    def __init__(self):
        if platform.system() == "Windows":
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
        super().__init__()
        # Hide until UI is built — avoids a brief empty white window on Windows.
        self.withdraw()
        self.title(APP_NAME)
        _icon = app_icon_path()
        if os.path.isfile(_icon):
            try:
                self.iconbitmap(_icon)
            except Exception:
                pass
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)

        _config_path = config_path()
        self._config_existed_at_startup = os.path.isfile(_config_path)
        self.cm = ConfigManager(_config_path)
        self.cm.load()
        app = self.cm.get_app()

        self.var_ide_paths = {ide: tk.StringVar(value=norm(self.cm.get_path(ide))) for ide in IDE_TYPES}
        self.var_base_dir = tk.StringVar(value=norm(app.get("base_dir", "")))
        self.var_open_new_window = tk.IntVar(value=int(app.get("open_new_window", "1")))
        self.var_reuse_existing_window = tk.IntVar(value=int(app.get("reuse_existing_window", "0")))
        self.var_extra_args = tk.StringVar(value=app.get("extra_args", ""))
        self.var_theme = tk.StringVar(value=self._normalize_theme(app.get("theme", "Dark")))
        self.var_ui_scale = tk.StringVar(value=(app.get("ui_scale", "Auto") or "Auto"))

        self.status = tk.StringVar(value=self._truncate_status(f"Config: {config_path()}"))

        self.base_font = tkfont.nametofont("TkDefaultFont")
        if os_name() == "Windows":
            try:
                self.base_font.configure(family="Segoe UI")
            except Exception:
                pass

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("alt")
        except Exception:
            try:
                self.style.theme_use("clam")
            except Exception:
                pass

        self.palette = self._palette_dark() if self._theme_is_dark() else self._palette_light()
        self._apply_style()
        self._apply_scale()
        self._build_ui()
        self._refresh_all_tabs()
        self._on_tab_changed()  # focus content, not tab label

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - self.WIDTH) // 2)
        y = max(0, (sh - self.HEIGHT) // 2)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        # “dotted focus” look: prevent focus by default
        self.bind_all("<Button-1>", self._defocus_on_click, add="+")

        global _app_ref
        _app_ref = self

        self.deiconify()
        self.lift()
        self.focus_force()

    def _defocus_on_click(self, e):
        try:
            if isinstance(e.widget, ttk.Button):
                return
            w = self.focus_get()
            if isinstance(w, ttk.Button):
                self.focus_set()
        except Exception:
            pass

    def _report_bugs_enter(self, _e=None) -> None:
        if hasattr(self, "report_bugs_lbl"):
            self.report_bugs_lbl.config(fg="red")

    def _report_bugs_leave(self, _e=None) -> None:
        if hasattr(self, "report_bugs_lbl"):
            self.report_bugs_lbl.config(fg=self.palette["muted"])

    def _palette_dark(self) -> dict:
        return {
            "bg": "#1E1E1E",
            "panel": "#252526",
            "panel2": "#2D2D2D",
            "border": "#3C3C3C",
            "text": "#D4D4D4",
            "muted": "#9DA2A6",
            "accent": "#007ACC",
            "accent_hover": "#1A8AD4",
            "accent_border": "#1A8AD4",
            "danger": "#F14C4C",
            "danger_hover": "#FF6B6B",
            "button_hover": "#4A4A4A",
            "warning": "#F14C4C",
            "field": "#1F1F1F",
            "select": "#094771",
            "button_border": "#5A5A5A",
        }

    def _palette_light(self) -> dict:
        return {
            "bg": "#F3F3F3",
            "panel": "#FFFFFF",
            "panel2": "#F6F6F6",
            "border": "#D0D0D0",
            "text": "#000000",
            "muted": "#000000",
            "accent": "#007ACC",
            "accent_hover": "#3399DD",
            "accent_border": "#0066B3",
            "danger": "#C62828",
            "danger_hover": "#E53935",
            "button_hover": "#D0D0D0",
            "warning": "#C62828",
            "field": "#FFFFFF",
            "select": "#CFE8FF",
            "button_border": "#909090",
        }

    def _apply_style(self) -> None:
        p = self.palette
        self.configure(bg=p["bg"])

        self.style.configure(".", background=p["bg"], foreground=p["text"])
        self.style.configure("TFrame", background=p["bg"])
        self.style.configure("TLabel", background=p["bg"], foreground=p["text"])
        self.style.configure("Muted.TLabel", background=p["bg"], foreground=p["muted"])
        self.style.configure("Card.TLabel", background=p["panel"], foreground=p["text"])
        self.style.configure("Warning.TLabel", background=p["panel"], foreground=p["warning"], font=(self.base_font.cget("family"), self.base_font.cget("size"), "normal"))

        self.style.configure("Card.TFrame", background=p["panel"], relief="flat", borderwidth=1, bordercolor=p["border"])
        self.style.configure(
            "Card.TCheckbutton",
            background=p["panel"],
            foreground=p["text"],
            indicatorsize=20,
        )
        self.style.map("Card.TCheckbutton", background=[("active", p["panel"])], foreground=[("active", p["text"])])
        self.style.configure(
            "Danger.TCheckbutton",
            background=p["panel"],
            foreground=p["danger"],
            indicatorsize=256,
        )
        self.style.map("Danger.TCheckbutton", background=[("active", p["panel"])], foreground=[("active", p["danger"])])

        self.style.configure("TEntry", fieldbackground=p["field"], foreground=p["text"])
        self.style.configure(
            "TCombobox",
            fieldbackground=p["field"],
            foreground=p["text"],
            background=p["panel2"],
            bordercolor=p["button_border"],
            borderwidth=1,
            padding=(6, 4),
            arrowcolor=p["text"],
        )
        # Keep text and field colors correct when dropdown is pressed/focused (fixes light theme text turning white)
        self.style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", p["field"]),
                ("focus", p["field"]),
                ("pressed", p["field"]),
            ],
            foreground=[
                ("readonly", p["text"]),
                ("focus", p["text"]),
                ("pressed", p["text"]),
            ],
            background=[
                ("readonly", p["panel2"]),
                ("focus", p["panel2"]),
                ("pressed", p["panel2"]),
            ],
            arrowcolor=[
                ("readonly", p["text"]),
                ("focus", p["text"]),
                ("pressed", p["text"]),
            ],
        )

        # Button layout with visible borders (clam: border attr sets size, relief="solid" draws it)
        try:
            self.style.layout(
                "TButton",
                [
                    (
                        "Button.border",
                        {"sticky": "nswe", "border": "2", "children": [
                            ("Button.focus", {"sticky": "nswe", "children": [
                                ("Button.padding", {"sticky": "nswe", "children": [("Button.label", {"sticky": "nswe"})]})
                            ]})
                        ]},
                    )
                ],
            )
        except Exception:
            pass
        self.style.configure(
            "TButton",
            background=p["panel2"],
            foreground=p["text"],
            padding=(8, 6),
            relief="solid",
            borderwidth=2,
            bordercolor=p["button_border"],
            darkcolor=p["panel2"],
            lightcolor=p["panel2"],
        )
        self.style.map(
            "TButton",
            background=[("active", p["button_hover"]), ("pressed", p["button_hover"])],
            bordercolor=[("active", p["button_border"]), ("pressed", p["button_border"])],
            darkcolor=[("active", p["button_hover"]), ("pressed", p["button_hover"])],
            lightcolor=[("active", p["button_hover"]), ("pressed", p["button_hover"])],
        )
        try:
            self.style.configure("TButton", focusthickness=0, focuspadding=0)
        except Exception:
            pass

        self.style.configure(
            "Accent.TButton",
            background=p["accent"],
            foreground="#FFFFFF",
            padding=(8, 6),
            relief="solid",
            borderwidth=2,
            bordercolor=p["accent_border"],
            darkcolor=p["accent"],
            lightcolor=p["accent"],
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", p["accent_hover"]), ("pressed", p["accent_hover"])],
            bordercolor=[("active", p["accent_border"]), ("pressed", p["accent_border"])],
            darkcolor=[("active", p["accent_hover"]), ("pressed", p["accent_hover"])],
            lightcolor=[("active", p["accent_hover"]), ("pressed", p["accent_hover"])],
        )

        self.style.configure(
            "Danger.TButton",
            background=p["panel2"],
            foreground=p["danger"],
            padding=(8, 6),
            relief="solid",
            borderwidth=2,
            bordercolor=p["button_border"],
            darkcolor=p["panel2"],
            lightcolor=p["panel2"],
        )
        self.style.map(
            "Danger.TButton",
            background=[("active", p["button_hover"]), ("pressed", p["button_hover"])],
            bordercolor=[("active", p["button_border"]), ("pressed", p["button_border"])],
            darkcolor=[("active", p["button_hover"]), ("pressed", p["button_hover"])],
            lightcolor=[("active", p["button_hover"]), ("pressed", p["button_hover"])],
        )

        self.style.configure("TSeparator", background=p["border"])
        self.style.configure("Treeview", background=p["field"], fieldbackground=p["field"], foreground=p["text"], relief="flat", borderwidth=0)
        self.style.map("Treeview", background=[("selected", p["select"])], foreground=[("selected", "#FFFFFF" if self._theme_is_dark() else p["text"])])

        # Notebook tabs: completely flat, no sunken, no focus outline
        if self._theme_is_dark():
            tab_bg_unsel = "#2D2D2D"
            tab_bg_sel = "#3C3C3C"
            tab_bg_hover = "#404040"
            tab_fg = "#FFFFFF"
        else:
            tab_bg_unsel = "#E8E8E8"
            tab_bg_sel = "#FFFFFF"
            tab_bg_hover = "#D8D8D8"
            tab_fg = "#1E1E1E"
        self.style.configure(
            "TNotebook",
            background=p["bg"],
            tabmargins=[2, 5, 2, 0],
            borderwidth=0,
            highlightbackground=p["bg"],
        )
        try:
            self.style.layout("TNotebook", [])
        except Exception:
            pass
        # Flat tab layout: no focus element, borderwidth 0, all colors match (no 3D)
        try:
            self.style.layout(
                "TNotebook.Tab",
                [
                    (
                        "Notebook.tab",
                        {
                            "sticky": "nswe",
                            "children": [
                                (
                                    "Notebook.padding",
                                    {
                                        "side": "top",
                                        "sticky": "nswe",
                                        "children": [("Notebook.label", {"side": "top", "sticky": ""})],
                                    },
                                )
                            ],
                        },
                    )
                ],
            )
        except Exception:
            pass
        self.style.configure(
            "TNotebook.Tab",
            background=tab_bg_unsel,
            foreground=tab_fg,
            padding=(12, 8),
            borderwidth=0,
            bordercolor=tab_bg_unsel,
            darkcolor=tab_bg_unsel,
            lightcolor=tab_bg_unsel,
        )
        self.style.map(
            "TNotebook.Tab",
            background=[
                ("selected", tab_bg_sel),
                ("active", tab_bg_hover),
            ],
            foreground=[
                ("selected", tab_fg),
                ("active", tab_fg),
            ],
            bordercolor=[
                ("selected", tab_bg_sel),
                ("active", tab_bg_hover),
            ],
            darkcolor=[
                ("selected", tab_bg_sel),
                ("active", tab_bg_hover),
            ],
            lightcolor=[
                ("selected", tab_bg_sel),
                ("active", tab_bg_hover),
            ],
        )

        if hasattr(self, "report_bugs_lbl"):
            self.report_bugs_lbl.config(fg=p["muted"], bg=p["bg"])
        for rail in getattr(self, "rails", []):
            if rail.winfo_exists():
                rail.configure(bg=p["bg"])
        for canvas in getattr(self, "rail_canvases", []):
            if canvas.winfo_exists():
                canvas.configure(bg=p["bg"])

    def _parse_ui_scale(self) -> float | None:
        v = (self.var_ui_scale.get() or "").strip()
        if v.lower() == "auto":
            return None
        if v.endswith("%"):
            try:
                pct = float(v[:-1])
                factor = pct / 100.0
                return (96.0 * factor) / 72.0
            except Exception:
                return None
        return None

    def _apply_scale(self) -> None:
        forced = self._parse_ui_scale()
        if forced is not None:
            self.tk.call("tk", "scaling", forced)
        else:
            dpi = get_windows_dpi()
            self.tk.call("tk", "scaling", dpi / 72.0)
        self.update_idletasks()
        self._update_tree_rowheight()

    def _update_tree_rowheight(self) -> None:
        linespace = self.base_font.metrics("linespace")
        self.style.configure("Treeview", rowheight=max(int(linespace + 16), 34))

    def _truncate_status(self, msg: str, max_len: int = 70) -> str:
        """Truncate long status messages; show end of path so filename is visible."""
        if len(msg) <= max_len:
            return msg
        return "..." + msg[-(max_len - 3) :]

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=4)
        root.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        top = ttk.Frame(root, style="Card.TFrame", padding=4)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        top.columnconfigure(3, weight=1)

        ttk.Label(top, text="Profiles Dir", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        self.entry_base_dir = ttk.Entry(top, textvariable=self.var_base_dir, width=50)
        self.entry_base_dir.grid(row=0, column=1, sticky="ew", padx=(4, 4))
        ttk.Button(top, text="Browse", command=self._browse_base, takefocus=False, cursor="hand2").grid(row=0, column=2, padx=(0, 4))

        ttk.Label(top, text="Theme", style="Card.TLabel").grid(row=0, column=3, sticky="e", padx=(8, 4))
        theme = ttk.Combobox(top, textvariable=self.var_theme, values=self.THEME_OPTIONS, state="readonly", width=6, cursor="hand2")
        theme.grid(row=0, column=4, sticky="e")

        def _blur_combobox(cb: ttk.Combobox) -> None:
            try:
                cb.selection_clear()
            except Exception:
                pass
            self.focus_set()

        def _on_theme_and_blur(e):
            self._on_theme_change()
            self.after(0, lambda: _blur_combobox(e.widget))

        def _on_scale_and_blur(e):
            self._on_scale_change()
            self.after(0, lambda: _blur_combobox(e.widget))

        theme.bind("<<ComboboxSelected>>", _on_theme_and_blur)

        ttk.Label(top, text="Scale", style="Card.TLabel").grid(row=0, column=5, sticky="e", padx=(4, 4))
        scale = ttk.Combobox(top, textvariable=self.var_ui_scale, values=self.SCALE_OPTIONS, state="readonly", width=6, cursor="hand2")
        scale.grid(row=0, column=6, sticky="e")
        scale.bind("<<ComboboxSelected>>", _on_scale_and_blur)

        self.entry_base_dir.config(state="disabled")

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        root.rowconfigure(1, weight=1)
        self.notebook.configure(takefocus=False)
        try:
            self.notebook.configure(cursor="hand2")
        except Exception:
            pass
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.trees: dict[str, ttk.Treeview] = {}
        self.ide_path_entries: dict[str, ttk.Entry] = {}
        self.rails: list[tk.Frame] = []
        self.rail_canvases: list[tk.Canvas] = []

        for ide in IDE_TYPES:
            tab = ttk.Frame(self.notebook, padding=4)
            self.notebook.add(tab, text=IDE_DISPLAY_NAMES.get(ide, ide))
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(1, weight=1)

            path_frm = ttk.Frame(tab, style="Card.TFrame", padding=4)
            path_frm.grid(row=0, column=0, sticky="ew", pady=(0, 4))
            path_frm.columnconfigure(1, weight=1)
            ttk.Label(path_frm, text="Path", style="Card.TLabel").grid(row=0, column=0, sticky="w")
            entry = ttk.Entry(path_frm, textvariable=self.var_ide_paths[ide], width=45)
            entry.grid(row=0, column=1, sticky="ew", padx=(4, 4))
            entry.config(state="disabled")
            self.ide_path_entries[ide] = entry
            ttk.Button(path_frm, text="Browse", command=lambda i=ide: self._browse_ide(i), takefocus=False, cursor="hand2").grid(row=0, column=2, padx=(0, 2))
            ttk.Button(path_frm, text="Detect", command=lambda i=ide: self._detect_ide(i), takefocus=False, cursor="hand2").grid(row=0, column=3)

            body = ttk.Frame(tab)
            body.grid(row=1, column=0, sticky="nsew")
            body.columnconfigure(0, weight=0, minsize=500)
            body.columnconfigure(1, weight=1, minsize=190)
            body.rowconfigure(0, weight=0)
            body.rowconfigure(1, weight=1)

            header_frm = ttk.Frame(body, style="Card.TFrame")
            header_frm.grid(row=0, column=0, sticky="ew", pady=(0, 2))
            header_frm.columnconfigure(0, weight=1)
            ttk.Label(header_frm, text="IDE Launcher Profiles", style="Card.TLabel", font=(self.base_font.cget("family"), self.base_font.cget("size") - 1, "bold")).grid(row=0, column=0, sticky="w", padx=(8, 6), pady=2)

            table = ttk.Frame(body)
            table.grid(row=1, column=0, sticky="nsew")
            table.columnconfigure(0, weight=1)
            table.rowconfigure(0, weight=1)
            tree = ttk.Treeview(table, columns=(), show="tree", height=5, takefocus=False)
            tree.column("#0", width=200, minwidth=100, stretch=True, anchor="w")
            tree.grid(row=0, column=0, sticky="nsew")
            vsb = ttk.Scrollbar(table, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            vsb.grid(row=0, column=1, sticky="ns", padx=(6, 0))
            tree.bind("<Double-1>", lambda e, i=ide: self._launch_for_ide(i))
            self.trees[ide] = tree

            rail = tk.Frame(body, bg=self.palette["bg"], cursor="hand2")
            rail.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(8, 0))
            rail.columnconfigure(0, weight=1)
            self.rails.append(rail)

            def rbtn(text, cmd, style="TButton", pady=(0, 2)):
                b = ttk.Button(rail, text=text, command=cmd, style=style, takefocus=False)
                b.pack(fill="x", pady=pady)
                try:
                    b.configure(cursor="hand2")
                except Exception:
                    pass
                return b

            rbtn("Launch Profile", lambda i=ide: self._launch_for_ide(i), style="Accent.TButton", pady=(0, 2))
            rbtn("Create Profile", lambda i=ide: self._add_profile(i), pady=(0, 2))
            rbtn("Edit Profile", lambda i=ide: self._edit_profile(i), pady=(0, 2))
            rbtn("Delete Profile", lambda i=ide: self._delete_profile(i), style="Danger.TButton", pady=(0, 2))
            ttk.Separator(rail).pack(fill="x", pady=(2, 3))
            rbtn("Open Profile Folder", lambda i=ide: self._open_profile_folder(i), pady=(0, 2))
            ttk.Separator(rail).pack(fill="x", pady=(2, 3))
            rbtn("Reload Profiles", self.reload_config, pady=(0, 0))

        status = ttk.Frame(root, padding=(2, 4, 2, 0))
        status.grid(row=2, column=0, sticky="ew")
        status.columnconfigure(0, weight=1)
        ttk.Label(status, textvariable=self.status, style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.report_bugs_lbl = tk.Label(
            status,
            text="Report Bugs?",
            fg=self.palette["muted"],
            bg=self.palette["bg"],
            cursor="hand2",
            font=(self.base_font.cget("family"), self.base_font.cget("size")),
        )
        self.report_bugs_lbl.grid(row=0, column=1, sticky="e")
        self.report_bugs_lbl.bind("<Enter>", self._report_bugs_enter)
        self.report_bugs_lbl.bind("<Leave>", self._report_bugs_leave)
        self.report_bugs_lbl.bind("<Button-1>", lambda _e: ReportBugsDialog(self))

    def _refresh_all_tabs(self) -> None:
        for ide in IDE_TYPES:
            tree = self.trees.get(ide)
            if not tree:
                continue
            for item in tree.get_children():
                tree.delete(item)
            for p in self.cm.get_profiles_for_ide(ide):
                tree.insert("", "end", text=p.name)
            kids = tree.get_children()
            if kids:
                tree.selection_set(kids[0])
                tree.focus(kids[0])

    def _on_tab_changed(self, _e=None) -> None:
        """Move focus from tab label to content so no dotted focus ring on tabs."""
        ide = self._current_ide()
        tree = self.trees.get(ide)
        if tree and tree.winfo_exists():
            tree.focus_set()

    def _current_ide(self) -> str:
        idx = self.notebook.index(self.notebook.select())
        return IDE_TYPES[idx] if idx < len(IDE_TYPES) else IDE_TYPES[0]

    def _selected_profile(self, ide: str) -> Profile | None:
        tree = self.trees.get(ide)
        if not tree:
            return None
        sel = tree.selection()
        if not sel:
            return None
        name = tree.item(sel[0], "text")
        if not name:
            return None
        for p in self.cm.get_profiles_for_ide(ide):
            if p.name == name:
                return p
        return None

    def _browse_ide(self, ide: str) -> None:
        title = f"Select {IDE_DISPLAY_NAMES.get(ide, ide)} executable"
        current = norm(self.var_ide_paths[ide].get())
        initialdir = None
        if current:
            if os.path.isfile(current):
                initialdir = os.path.dirname(current)
            elif os.path.isdir(current):
                initialdir = current
            else:
                initialdir = os.path.dirname(current) if os.path.dirname(current) else None
        if os_name() == "Windows":
            fp = filedialog.askopenfilename(
                title=title,
                filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
                initialdir=initialdir,
            )
        else:
            fp = filedialog.askopenfilename(title=title, initialdir=initialdir)
        if fp:
            self.ide_path_entries[ide].config(state="normal")
            self.var_ide_paths[ide].set(norm(fp))
            self.ide_path_entries[ide].config(state="disabled")

    def _detect_ide(self, ide: str) -> None:
        p = autodetect_ide_path(ide)
        if p:
            p = resolve_ide_exe(norm(p), ide)  # prefer .exe over bin/cursor script
            self.ide_path_entries[ide].config(state="normal")
            self.var_ide_paths[ide].set(p)
            self.ide_path_entries[ide].config(state="disabled")
            self.status.set(f"Detected {IDE_DISPLAY_NAMES.get(ide, ide)}: {p}")
        else:
            d = InfoDialog(self, APP_NAME, f"Could not auto-detect {IDE_DISPLAY_NAMES.get(ide, ide)}.")
            self.wait_window(d)

    def _browse_base(self):
        initialdir = norm(self.var_base_dir.get()) if self.var_base_dir.get() else None
        if initialdir and not os.path.isdir(initialdir):
            initialdir = os.path.dirname(initialdir) if os.path.dirname(initialdir) else None
        d = filedialog.askdirectory(title="Select Profiles Directory", initialdir=initialdir)
        if d:
            self.entry_base_dir.config(state="normal")
            self.var_base_dir.set(norm(d))
            self.entry_base_dir.config(state="disabled")

    def _on_theme_change(self):
        self.palette = self._palette_dark() if self._theme_is_dark() else self._palette_light()
        self._apply_style()
        self._apply_scale()

    def _on_scale_change(self):
        self._apply_scale()
        self._apply_style()  # Reapply styles so fonts/row heights reflect new scaling
        d = SaveAndRelaunchConfirmDialog(self)
        self.wait_window(d)
        if not d.confirmed:
            return
        self._write_config_to_disk()
        self._relaunch()

    def _add_profile(self, ide: str) -> None:
        existing_lower = {p.name.lower() for p in self.cm.get_profiles_for_ide(ide)}
        suggested = "Profile1"
        for i in range(1, 999):
            cand = f"Profile{i}"
            if cand.lower() not in existing_lower:
                suggested = cand
                break
        d = AddProfileDialog(self, ide, suggested)
        self.wait_window(d)
        if not d.result:
            return
        name = d.result.strip()
        if name.lower() in {p.name.lower() for p in self.cm.get_profiles_for_ide(ide)}:
            d = InfoDialog(self, APP_NAME, "Profile name already exists.")
            self.wait_window(d)
            return
        p = make_profile_from_name(ide, name, self.var_base_dir.get())
        p.ensure_folders()
        self.cm.upsert_profile(p)
        self._refresh_all_tabs()
        self._write_config_to_disk()

    def _edit_profile(self, ide: str) -> None:
        p = self._selected_profile(ide)
        if not p:
            d = InfoDialog(self, APP_NAME, "Select a profile first.")
            self.wait_window(d)
            return
        d = EditProfileDialog(self, ide, p.name)
        self.wait_window(d)
        if not d.result:
            return
        new_name = d.result.strip()
        if new_name.lower() != p.name.lower():
            existing = [x.name.lower() for x in self.cm.get_profiles_for_ide(ide) if x.name.lower() != p.name.lower()]
            if new_name.lower() in existing:
                d = InfoDialog(self, APP_NAME, "Another profile with that name already exists.")
                self.wait_window(d)
                return
        if new_name != p.name:
            old_folder = p.codex_home if p.ide == "codex" else os.path.dirname(p.user_data)
            new_p = make_profile_from_name(ide, new_name, self.var_base_dir.get())
            new_folder = new_p.codex_home if new_p.ide == "codex" else os.path.dirname(new_p.user_data)
            if old_folder != new_folder:
                if os.path.isdir(old_folder):
                    if os.path.exists(new_folder):
                        d = InfoDialog(self, APP_NAME, f"A folder already exists at:\n{new_folder}\nCannot rename.")
                        self.wait_window(d)
                        return
                    try:
                        shutil.move(old_folder, new_folder)
                    except Exception as e:
                        d = InfoDialog(self, APP_NAME, f"Could not rename folder:\n\n{e}")
                        self.wait_window(d)
                        return
                else:
                    new_p.ensure_folders()
            self.cm.delete_profile(ide, p.name)
            self.cm.upsert_profile(new_p)
        self._refresh_all_tabs()
        self._write_config_to_disk()

    def _delete_profile(self, ide: str) -> None:
        p = self._selected_profile(ide)
        if not p:
            d = InfoDialog(self, APP_NAME, "Select a profile first.")
            self.wait_window(d)
            return
        d = DeleteConfirmDialog(self, p.name, p)
        self.wait_window(d)
        if not d.confirmed:
            return
        if d.delete_from_disk:
            folder = p.codex_home if p.ide == "codex" else os.path.dirname(p.user_data)
            if folder and os.path.isdir(folder):
                try:
                    shutil.rmtree(folder)
                    self.status.set(f"Removed profile and deleted: {folder}")
                except Exception as e:
                    d = InfoDialog(self, APP_NAME, f"Could not delete folder:\n\n{e}")
                    self.wait_window(d)
        self.cm.delete_profile(ide, p.name)
        self._refresh_all_tabs()
        self._write_config_to_disk()

    def _open_profile_folder(self, ide: str) -> None:
        p = self._selected_profile(ide)
        if not p:
            d = InfoDialog(self, APP_NAME, "Select a profile first.")
            self.wait_window(d)
            return
        open_folder_cross_platform(p.folder_path())

    def open_base_dir(self):
        open_folder_cross_platform(self.var_base_dir.get())

    def _write_config_to_disk(self) -> None:
        """Write current UI state to config file (no dialogs)."""
        self.cm.set_app("base_dir", norm(self.var_base_dir.get()))
        self.cm.set_app("open_new_window", "1" if self.var_open_new_window.get() else "0")
        self.cm.set_app("reuse_existing_window", "1" if self.var_reuse_existing_window.get() else "0")
        self.cm.set_app("extra_args", (self.var_extra_args.get() or "").strip())
        self.cm.set_app("theme", self.var_theme.get())
        self.cm.set_app("ui_scale", self.var_ui_scale.get())
        for ide in IDE_TYPES:
            self.cm.set_path(ide, norm(self.var_ide_paths[ide].get()))
        self.cm.save()
        self.status.set(self._truncate_status(f"Saved config: {config_path()}"))

    def _relaunch(self) -> None:
        """Start a new process and exit so the new UI scale takes effect."""
        try:
            cwd = app_dir()
            if getattr(sys, "frozen", False) and platform.system() == "Windows":
                os.startfile(sys.executable)
            else:
                kwargs = {"cwd": cwd}
                if platform.system() == "Windows":
                    kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
                if getattr(sys, "frozen", False):
                    subprocess.Popen([sys.executable], **kwargs)
                else:
                    subprocess.Popen([sys.executable, os.path.abspath(__file__)], **kwargs)
            self.after(600, self._exit_after_relaunch)
        except Exception:
            InfoDialog(
                self,
                "Auto relaunch failed",
                "Auto relaunch failed. You can manually close and open the program to apply the new UI scale.",
            )

    def _exit_after_relaunch(self) -> None:
        self.quit()
        sys.exit(0)

    def save_config(self):
        d = SaveConfirmDialog(self)
        self.wait_window(d)
        if not d.confirmed:
            return
        self._write_config_to_disk()
        d = InfoDialog(self, "Configuration saved", "Your settings have been written to the config file.")
        self.wait_window(d)

    def reload_config(self) -> None:
        self.cm.load()
        self.cm.recheck_all_paths()
        app = self.cm.get_app()
        for ide in IDE_TYPES:
            self.var_ide_paths[ide].set(norm(self.cm.get_path(ide)))
        self.var_base_dir.set(norm(app.get("base_dir", "")))
        self.var_open_new_window.set(int(app.get("open_new_window", "1")))
        self.var_reuse_existing_window.set(int(app.get("reuse_existing_window", "0")))
        self.var_extra_args.set(app.get("extra_args", ""))
        self.var_theme.set(self._normalize_theme(app.get("theme", "Dark")))
        self.var_ui_scale.set(app.get("ui_scale", "Auto") or "Auto")

        self.palette = self._palette_dark() if self._theme_is_dark() else self._palette_light()
        self._apply_style()
        self._apply_scale()
        self._refresh_all_tabs()
        self._on_tab_changed()
        self.status.set(self._truncate_status(f"Reloaded config: {config_path()}"))

    def _launch_for_ide(self, ide: str) -> None:
        p = self._selected_profile(ide)
        if not p:
            d = InfoDialog(self, APP_NAME, "Select a profile first.")
            self.wait_window(d)
            return

        exe = norm(self.var_ide_paths[ide].get())
        exe = resolve_ide_exe(exe, ide)  # resolve bin/cursor etc. to Cursor.exe
        if not is_executable_path(exe):
            d = InfoDialog(self, APP_NAME, f"{IDE_DISPLAY_NAMES.get(ide, ide)} path is invalid. Set it in the tab.")
            self.wait_window(d)
            return

        p.ensure_folders()

        try:
            if ide == "codex":
                env = os.environ.copy()
                env["CODEX_HOME"] = p.codex_home
                subprocess.Popen([exe], env=env, cwd=os.path.dirname(exe) if os.path.isfile(exe) else None)
            else:
                args = [
                    exe,
                    "--user-data-dir", p.user_data,
                    "--extensions-dir", p.extensions,
                ]
                if self.var_open_new_window.get() and not self.var_reuse_existing_window.get():
                    args.append("--new-window")
                args.extend(split_args(self.var_extra_args.get()))
                subprocess.Popen(args, cwd=os.path.dirname(exe) if os.path.isfile(exe) else None)
            self.status.set(f"Launched {p.name}")
        except Exception as e:
            d = InfoDialog(self, APP_NAME, f"Launch failed:\n\n{e}")
            self.wait_window(d)


# --- Global excepthook ---

def _global_excepthook(exc_type: type, exc_value: BaseException, exc_tb) -> None:
    """Log to crash.log; show report-bugs modal or fallback."""
    err = traceback.format_exc()
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(crash_log_path(), "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"{stamp}\n")
            f.write(err)
    except Exception:
        pass
    short = (str(exc_value) or exc_type.__name__).strip() or "Unknown error"
    try:
        if _app_ref and _app_ref.winfo_exists():
            _app_ref.after(0, lambda: ReportBugsDialog(_app_ref, error_message=short))
        else:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                APP_NAME,
                f"An unexpected error occurred.\n\n{short}\n\n"
                f"Please report at: {REPORT_BUGS_URL}",
            )
            root.destroy()
    except Exception:
        pass


# --- Entry ---

def run_app():
    sys.excepthook = _global_excepthook
    app = App()
    app.mainloop()

def crash_safe_main():
    try:
        run_app()
    except Exception:
        err = traceback.format_exc()
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(crash_log_path(), "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"{stamp}\n")
                f.write(err)
        except Exception:
            pass

        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                APP_NAME,
                "App crashed on startup.\n\n"
                "A crash.log file was created beside the EXE.\n\n"
                "Error:\n" + err.splitlines()[-1]
            )
            root.destroy()
        except Exception:
            pass

if __name__ == "__main__":
    crash_safe_main()