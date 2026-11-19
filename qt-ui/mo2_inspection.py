"""Read-only inspection for Mod Organizer 2 and STL compatibility setup.

This module deliberately does not create directories, edit Steam VDF files, alter
prefixes, or modify existing MO2 instances. It only reports discovered paths.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil

APP_ID = "489830"
STEAM_CANDIDATES = (
    ".steam/steam",
    ".local/share/Steam",
    ".steam/root",
    ".var/app/com.valvesoftware.Steam/.local/share/Steam",
)


def find_steam_roots(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    roots: list[Path] = []
    for relative in STEAM_CANDIDATES:
        path = home / relative
        if (path / "steamapps").is_dir():
            resolved = path.resolve()
            if resolved not in roots:
                roots.append(resolved)
    return roots


def find_mo2_installations(home: Path | None = None) -> list[Path]:
    """Find common MO2 Linux/Proton locations without traversing whole disks."""
    home = home or Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    candidates = [
        config / "steamtinkerlaunch/mo2/compatdata/pfx/drive_c/Modding/MO2",
        config / "stl/mo2/compatdata/pfx/drive_c/Modding/MO2",
        home / "Games/ModOrganizer",
        home / "Games/Mod Organizer 2",
        home / ".local/share/Steam/steamapps/compatdata/489830/pfx/drive_c/Modding/MO2",
        home / ".local/share/ModOrganizer",
        home / ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/489830/pfx/drive_c/Modding/MO2",
    ]
    for root in find_steam_roots(home):
        candidates.append(root / "steamapps/compatdata/489830/pfx/drive_c/Modding/MO2")
    found: list[Path] = []
    for candidate in candidates:
        executable = candidate / "ModOrganizer.exe"
        if executable.is_file():
            resolved = candidate.resolve()
            if resolved not in found:
                found.append(resolved)
    return found


def inspect_stl_installation(home: Path | None = None) -> dict:
    """Inspect the user-local STL install, PATH, and common compatibility-tool folders."""
    home = home or Path.home()
    data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
    local_install = data_home / "stl-steam"
    candidates = [
        local_install / "bin/steamtinkerlaunch",
        home / ".steam/root/compatibilitytools.d/SteamTinkerLaunch/steamtinkerlaunch",
        home / ".steam/root/compatibilitytools.d/steamtinkerlaunch/steamtinkerlaunch",
        home / ".local/share/Steam/compatibilitytools.d/SteamTinkerLaunch/steamtinkerlaunch",
        home / ".local/share/Steam/compatibilitytools.d/steamtinkerlaunch/steamtinkerlaunch",
    ]
    path_executable = shutil.which("steamtinkerlaunch")
    if path_executable:
        candidates.append(Path(path_executable))
    existing = []
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            resolved = candidate.resolve()
            if resolved not in existing:
                existing.append(resolved)
    return {
        "installed": bool(existing),
        "executables": [str(path) for path in existing],
        "local_install": str(local_install),
        "compatibility_tool_present": any("compatibilitytools.d" in str(p) for p in existing),
    }


def inspect_mo2(home: Path | None = None) -> dict:
    installations = find_mo2_installations(home)
    return {
        "found": bool(installations),
        "installations": [str(path) for path in installations],
        "note": "Detection only. Existing MO2 instances and prefixes are not modified.",
    }


def inspect_skyrim_compatibility(steam_root: Path, app_id: str = APP_ID) -> dict:
    """Read the app's localconfig.vdf and report whether it mentions STL.

    This is intentionally a conservative textual inspection, not a VDF writer.
    It never changes the file and does not claim that a mention proves a valid
    compatibility-tool installation.
    """
    candidates = [
        steam_root / "userdata",
        steam_root.parent / "userdata",
    ]
    files: list[Path] = []
    for userdata in candidates:
        if not userdata.is_dir():
            continue
        try:
            files.extend(userdata.glob(f"*/config/localconfig.vdf"))
        except OSError:
            pass
    seen: set[str] = set()
    matches = []
    for path in files:
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        # Scope the approximate match to app id block to avoid unrelated games.
        app_match = re.search(rf'"{re.escape(app_id)}"\s*\{{', text)
        if not app_match:
            continue
        chunk = text[app_match.end():app_match.end() + 12000]
        stl = re.search(r"steamtinkerlaunch|stl-steam", chunk, re.IGNORECASE)
        if stl:
            resolved = str(path.resolve())
            if resolved not in seen:
                seen.add(resolved)
                matches.append(resolved)
    return {
        "files_checked": [str(path) for path in files],
        "stl_reference_found": bool(matches),
        "matching_configs": matches,
        "note": "Steam's compatibility selection is only inspected; no VDF file is edited.",
    }
