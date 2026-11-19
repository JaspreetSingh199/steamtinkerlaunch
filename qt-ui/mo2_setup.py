"""Thin, guarded wrappers around SteamTinkerLaunch's documented MO2 CLI."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

from stl_compatibility import find_stl_executable

APP_ID = "489830"


def mo2_prefix_candidates(home: Path | None = None) -> list[Path]:
    """Potential prefix paths from STL's MO2 defaults, for inspection only."""
    home = home or Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    return [
        config / "steamtinkerlaunch/compatdata/pfx",
        config / "steamtinkerlaunch/mo2/compatdata/pfx",
    ]


def mo2_executable_candidates(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    return [prefix / "drive_c/Modding/MO2/ModOrganizer.exe" for prefix in mo2_prefix_candidates(home)]


def inspect_mo2_installation(home: Path | None = None) -> dict:
    candidates = mo2_executable_candidates(home)
    found = [path.resolve() for path in candidates if path.is_file()]
    return {
        "installed": bool(found),
        "executables": [str(path) for path in found],
        "candidates": [str(path) for path in candidates],
        "prefixes": [str(path) for path in mo2_prefix_candidates(home)],
    }


def _run_stl(args: list[str], home: Path, timeout: int = 120) -> dict:
    stl = find_stl_executable(home)
    if stl is None:
        return {"ok": False, "message": "STL executable not found. Install STL-Steam first."}
    try:
        result = subprocess.run([str(stl), *args], check=False, capture_output=True,
                                text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "message": f"STL command timed out: {' '.join(args)}"}
    except OSError as error:
        return {"ok": False, "message": f"Could not start STL: {error}"}
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    if result.returncode != 0:
        return {"ok": False, "message": f"STL command failed ({result.returncode}): {' '.join(args)}",
                "output": output, "returncode": result.returncode}
    return {"ok": True, "output": output, "returncode": result.returncode}


def inspect_mo2_instance_list(home: Path | None = None) -> dict:
    """Use STL's own MO2 instance registry; this is authoritative for custom MO2COMPDATA."""
    home = home or Path.home()
    stl = find_stl_executable(home)
    if stl is None:
        return {"ok": False, "installed": False, "message": "STL executable not found."}
    try:
        result = subprocess.run([str(stl), "mo2", "list-installed"], check=False,
                                capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return {"ok": False, "installed": False, "message": "STL's MO2 instance listing timed out."}
    except OSError as error:
        return {"ok": False, "installed": False, "message": f"Could not run STL's MO2 instance listing: {error}"}
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    found = [line.strip() for line in output.splitlines()
             if "Mod Organizer" in line or "MO2" in line or "(489830)" in line]
    return {"ok": result.returncode == 0, "installed": bool(found),
            "instances": found, "output": output,
            "message": "STL returned installed MO2 instance entries." if found else "STL did not report any installed MO2 instances."}


def run_mo2_command(command: str, home: Path | None = None, *, dry_run: bool = True) -> dict:
    """Prepare a visible STL MO2 command; GUI commands must not be captured into a hidden subprocess."""
    if command not in {"install", "start"}:
        return {"ok": False, "dry_run": dry_run, "message": "Unsupported MO2 command."}
    home = home or Path.home()
    stl = find_stl_executable(home)
    if stl is None:
        return {"ok": False, "dry_run": dry_run,
                "message": "SteamTinkerLaunch executable was not found. Install it from Compatibility first."}
    state = inspect_mo2_installation(home)
    if command == "install" and state["installed"]:
        return {"ok": False, "dry_run": dry_run,
                "message": "MO2.exe is already present in a known location. Installation was not started, to protect the existing copy.",
                "existing": state["executables"]}
    command_line = [str(stl), "mo2", command]
    if dry_run:
        return {"ok": True, "dry_run": True,
                "message": f"Ready to start STL's visible MO2 {command} window.",
                "command": command_line}
    try:
        process = subprocess.Popen(command_line, stdin=None, stdout=None, stderr=None,
                                   start_new_session=True)
    except OSError as error:
        return {"ok": False, "dry_run": False,
                "message": f"Could not start STL's MO2 {command} process: {error}",
                "next_step": "Check that the executable exists and is marked executable. No MO2 data was changed by this app."}
    return {"ok": True, "dry_run": False,
            "message": f"Started STL's MO2 {command} process (PID {process.pid}). The installer window/output should be visible separately. This confirms start only, not installation completion.",
            "pid": process.pid, "command": command_line,
            "verification": "Not yet verified. After the visible process completes, use Check Skyrim MO2 instance."}


def inspect_skyrim_mo2_instance(home: Path | None = None) -> dict:
    state = inspect_mo2_instance_list(home)
    if not state.get("ok"):
        return {"ok": False, "installed": False,
                "message": state.get("message", "Could not inspect MO2 instances."),
                "output": state.get("output", "")}
    skyrim_entries = [line for line in state.get("instances", []) if "(489830)" in line]
    found = bool(skyrim_entries)
    return {"ok": True, "installed": found, "output": state.get("output", ""),
            "instances": state.get("instances", []),
            "message": "Skyrim SE MO2 instance detected." if found else (
                "STL is working, but it does not list a Skyrim SE MO2 instance yet. "
                "Next: open MO2 standalone, create/select the Skyrim Special Edition instance, then check again."
            )}


def create_skyrim_mo2_instance(home: Path | None = None, *, dry_run: bool = True) -> dict:
    """Ask STL to create its supported Skyrim SE instance; no manual INI creation."""
    home = home or Path.home()
    stl = find_stl_executable(home)
    if stl is None:
        return {"ok": False, "dry_run": dry_run, "message": "STL executable not found."}
    mo2 = inspect_mo2_installation(home)
    # MO2COMPDATA is configurable in STL. If common paths do not match, rely on
    # STL's own command and installed-instance verification rather than guessing.
    before = inspect_skyrim_mo2_instance(home)
    if before.get("installed"):
        return {"ok": False, "dry_run": dry_run,
                "message": "STL already lists a Skyrim SE instance. It was not modified.",
                "instance": before["output"]}
    if dry_run:
        return {"ok": True, "dry_run": True,
                "message": "Would run: steamtinkerlaunch mo2 create-instance 489830",
                "common_path_mo2_detected": mo2["installed"],
                "note": "STL validates its effective MO2 prefix, including custom MO2COMPDATA."}
    result = _run_stl(["mo2", "create-instance", APP_ID], home, timeout=180)
    if not result["ok"]:
        return {**result, "dry_run": False}
    after = inspect_skyrim_mo2_instance(home)
    if after.get("installed"):
        return {"ok": True, "dry_run": False,
                "message": "STL created and verified the Skyrim SE MO2 instance.",
                "output": result["output"], "instance": after["output"]}
    return {"ok": False, "dry_run": False,
            "message": (
                "STL completed the create-instance command, but its own installed-instance list still does not contain Skyrim SE (AppID 489830).\n\n"
                "Next: open MO2 standalone and create/select the Skyrim Special Edition instance there, then use 'Check Skyrim MO2 instance' again.\n"
                "No existing game files, saves, mods or MO2 instances were deleted."
            ),
            "output": result["output"], "verification": after.get("output", after.get("message"))}
