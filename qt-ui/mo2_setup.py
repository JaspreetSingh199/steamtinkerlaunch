"""Safe MO2 installation and standalone-launch wrappers around upstream STL.

The default actions are dry-run. Real actions are opt-in and refuse to install
over a detected MO2 executable in common locations.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
from stl_compatibility import find_stl_executable

def mo2_executable_candidates(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    return [
        config / "steamtinkerlaunch/mo2/compatdata/pfx/drive_c/Modding/MO2/ModOrganizer.exe",
        config / "stl/mo2/compatdata/pfx/drive_c/Modding/MO2/ModOrganizer.exe",
        home / ".local/share/Steam/steamapps/compatdata/489830/pfx/drive_c/Modding/MO2/ModOrganizer.exe",
    ]

def inspect_mo2_installation(home: Path | None = None) -> dict:
    candidates = mo2_executable_candidates(home)
    found = [path.resolve() for path in candidates if path.is_file()]
    return {"installed": bool(found), "executables": [str(path) for path in found],
            "candidates": [str(path) for path in candidates]}

def run_mo2_command(command: str, home: Path | None = None, *, dry_run: bool = True) -> dict:
    if command not in {"install", "start"}:
        return {"ok": False, "dry_run": dry_run, "message": "Unsupported MO2 command."}
    home = home or Path.home()
    stl = find_stl_executable(home)
    if stl is None:
        return {"ok": False, "dry_run": dry_run, "message": "STL executable not found. Install STL-Steam first."}
    state = inspect_mo2_installation(home)
    if command == "install" and state["installed"]:
        return {"ok": False, "dry_run": dry_run, "message": "MO2 is already installed in a detected location. Existing installation was not touched.", "existing": state["executables"]}
    if command == "start" and not state["installed"]:
        return {"ok": False, "dry_run": dry_run, "message": "MO2 is not detected. Install it first to avoid an implicit install during launch."}
    if dry_run:
        return {"ok": True, "dry_run": True, "message": f"Would run: steamtinkerlaunch mo2 {command}", "executable": str(stl)}
    try:
        result = subprocess.run([str(stl), "mo2", command], check=False, capture_output=True,
                               text=True, timeout=180 if command == "install" else 120)
    except subprocess.TimeoutExpired:
        return {"ok": False, "dry_run": False, "message": f"STL MO2 {command} timed out. No automatic cleanup was attempted."}
    except OSError as error:
        return {"ok": False, "dry_run": False, "message": f"Could not start STL MO2 {command}: {error}"}
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    if result.returncode != 0:
        return {"ok": False, "dry_run": False, "message": f"STL MO2 {command} failed with exit code {result.returncode}.", "output": output}
    state_after = inspect_mo2_installation(home)
    if command == "install" and not state_after["installed"]:
        return {"ok": False, "dry_run": False, "message": "STL reported success, but MO2 executable was not found in expected paths.", "output": output, "candidates": state_after["candidates"]}
    return {"ok": True, "dry_run": False, "message": f"STL MO2 {command} completed.", "output": output, "executables": state_after["executables"]}
