"""Open a creative project in the right installed app (Windows-first, falls back to the folder).

Vision never drives the app; it only launches it pointed at the project.
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

# project type -> ordered app keys to try
TYPE_APPS = {
    "music": ["ardour", "audacity"],
    "design": ["inkscape", "krita", "blender"],
    "video": ["obs", "blender"],
    "photo": ["krita", "inkscape"],
    "writing": ["obsidian"],
    "game": ["godot", "blender"],
}

# app key -> (executable names for PATH lookup, glob patterns for common install dirs)
APPS = {
    "ardour": (["ardour8", "ardour"], ["C:/Program Files/Ardour*/bin/Ardour*.exe"]),
    "audacity": (["audacity"], ["C:/Program Files/Audacity/Audacity.exe"]),
    "inkscape": (["inkscape"], ["C:/Program Files/Inkscape/bin/inkscape.exe"]),
    "krita": (["krita"], ["C:/Program Files/Krita*/bin/krita.exe", "~/tools/krita*/bin/krita.exe", "~/tools/krita*/*/bin/krita.exe"]),
    "blender": (["blender"], ["C:/Program Files/Blender Foundation/Blender*/blender.exe", "~/tools/blender*/blender.exe"]),
    "obs": (["obs64", "obs"], ["C:/Program Files/obs-studio/bin/64bit/obs64.exe"]),
    "obsidian": (["obsidian"], ["~/AppData/Local/Programs/Obsidian/Obsidian.exe"]),
    "godot": (["godot"], ["~/AppData/Local/Microsoft/WinGet/Packages/GodotEngine*/Godot*.exe"]),
}


def find_app(key: str) -> Optional[str]:
    names, patterns = APPS[key]
    for n in names:
        found = shutil.which(n)
        if found:
            return found
    for pat in patterns:
        hits = sorted(glob.glob(os.path.expanduser(pat)))
        hits = [h for h in hits if "console" not in h.lower()]
        if hits:
            return hits[0]
    return None


def resolve(project_type: str, app: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    """Return (app_key, executable) for the first installed candidate, or (None, None)."""
    candidates = [app] if app else TYPE_APPS.get(project_type, [])
    for key in candidates:
        if key not in APPS:
            raise ValueError(f"unknown app {key!r}; choose from {sorted(APPS)}")
        exe = find_app(key)
        if exe:
            return key, exe
    return None, None


def open_project(project_dir: Path, project_type: str, app: Optional[str] = None) -> str:
    """Launch the app detached (or open the folder). Returns a description of what happened."""
    key, exe = resolve(project_type, app)
    if exe:
        subprocess.Popen([exe], cwd=str(project_dir), close_fds=True)
        return f"launched {key} ({exe})"
    if os.name == "nt":
        os.startfile(str(project_dir))  # type: ignore[attr-defined]
        return "no matching app installed; opened the folder"
    opener = shutil.which("xdg-open")
    if opener:
        subprocess.Popen([opener, str(project_dir)])
        return "no matching app installed; opened the folder"
    return "no matching app installed"
