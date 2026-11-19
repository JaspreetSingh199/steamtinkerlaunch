"""Safe SteamTinkerLaunch compatibility-tool installation wrapper.
Dry-run is the default. Installation delegates to upstream's compat add and
refuses to proceed if a Steam compatibility-tool target already exists.
"""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import subprocess

TOOL_DIR_NAME = "SteamTinkerLaunch"

def find_stl_executable(home: Path | None = None) -> Path | None:
    home = home or Path.home()
    candidates = [home / ".local/share/stl-steam/bin/steamtinkerlaunch",
                  home / ".local/share/SteamTinkerLaunch/bin/steamtinkerlaunch"]
    found = shutil.which("steamtinkerlaunch")
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    return None

def find_steam_roots(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    candidates = [home / ".steam/root", home / ".steam/steam",
                  home / ".local/share/Steam",
                  home / ".var/app/com.valvesoftware.Steam/.local/share/Steam"]
    roots = []
    for candidate in candidates:
        if (candidate / "steamapps").is_dir():
            resolved = candidate.resolve()
            if resolved not in roots:
                roots.append(resolved)
    return roots

def compatibility_tool_targets(home: Path | None = None) -> list[Path]:
    return [root / "compatibilitytools.d" / TOOL_DIR_NAME for root in find_steam_roots(home)]

def inspect_compatibility_tool(home: Path | None = None) -> dict:
    targets = compatibility_tool_targets(home)
    present = [target for target in targets if target.exists() or target.is_symlink()]
    executable = find_stl_executable(home)
    return {"installed": bool(present), "targets": [str(p) for p in targets],
            "existing": [str(p) for p in present],
            "executable": str(executable) if executable else None}

def install_compatibility_tool(home: Path | None = None, *, dry_run: bool = True) -> dict:
    """Use upstream compat add; default is non-mutating dry-run."""
    home = home or Path.home()
    executable = find_stl_executable(home)
    if executable is None:
        return {"ok": False, "dry_run": dry_run, "message": "STL executable not found. Install STL-Steam first."}
    roots = find_steam_roots(home)
    if not roots:
        return {"ok": False, "dry_run": dry_run, "message": "No Steam root with steamapps was detected."}
    targets = compatibility_tool_targets(home)
    existing = [p for p in targets if p.exists() or p.is_symlink()]
    if existing:
        return {"ok": False, "dry_run": dry_run,
                "message": "An STL compatibility-tool directory already exists. It was left untouched.",
                "existing": [str(p) for p in existing]}
    if dry_run:
        return {"ok": True, "dry_run": True,
                "message": "Would run the upstream command: steamtinkerlaunch compat add",
                "executable": str(executable), "targets": [str(p) for p in targets]}
    try:
        completed = subprocess.run([str(executable), "compat", "add"], check=False,
                                  capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return {"ok": False, "dry_run": False,
                "message": "STL compat add timed out. No automatic cleanup was attempted."}
    except OSError as error:
        return {"ok": False, "dry_run": False, "message": f"Could not start STL compat add: {error}"}
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
    if completed.returncode:
        return {"ok": False, "dry_run": False,
                "message": f"Upstream STL compat add failed with exit code {completed.returncode}.",
                "output": output}
    state = inspect_compatibility_tool(home)
    if state["installed"]:
        return {"ok": True, "dry_run": False,
                "message": "STL compatibility tool installed and detected.",
                "output": output, "existing": state["existing"]}
    return {"ok": False, "dry_run": False,
            "message": "STL compat add exited successfully, but its target could not be verified.",
            "output": output, "targets": state["targets"]}
