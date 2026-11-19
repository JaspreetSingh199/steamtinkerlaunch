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


def run_mo2_command(command: str, home: Path | None = None, *, dry_run: bool = True) -> dict:
    if command not in {"install", "start"}:
        return {"ok": False, "dry_run": dry_run, "message": "Unsupported MO2 command."}
    home = home or Path.home()
    state = inspect_mo2_installation(home)
    if command == "install" and state["installed"]:
        return {"ok": False, "dry_run": dry_run,
                "message": "MO2 is already detected in a known STL/default prefix. Existing installation was not touched.",
                "existing": state["executables"]}
    if command == "start" and not state["installed"]:
        return {"ok": False, "dry_run": dry_run,
                "message": "MO2.exe was not found in common paths. Check STL's configured MO2COMPDATA or use its list-installed command before starting.",
                "candidates": state["candidates"]}
    if dry_run:
        return {"ok": True, "dry_run": True, "message": f"Would run: steamtinkerlaunch mo2 {command}"}
    result = _run_stl(["mo2", command], home, timeout=240 if command == "install" else 120)
    if not result["ok"]:
        return {**result, "dry_run": False}
    after = inspect_mo2_installation(home)
    if command == "install" and not after["installed"]:
        return {"ok": False, "dry_run": False,
                "message": (
                    "STL finished its install command, but this app could not find MO2.exe. "
                    "MO2 is NOT verified yet.\n\n"
                    "Next steps:\n"
                    "1. Open the Logs page and review/copy the STL output.\n"
                    "2. Go back to MO2 Setup and click 'Check Skyrim MO2 instance'.\n"
                    "3. If no instance is found, click 'Start MO2 standalone'. In MO2, create or select a Skyrim Special Edition instance.\n"
                    "4. Return here and click 'Check Skyrim MO2 instance' again.\n\n"
                    "Do not reinstall MO2 yet. It may be installed in a custom location that this app does not detect."
                ),
                "output": result["output"], "executables": after["executables"],
                "candidates": after["candidates"],
                "verification": "STL command exit status only; MO2 executable not verified."}
    return {"ok": True, "dry_run": False,
            "message": f"STL MO2 {command} command completed and MO2 was verified." if command == "install" else "STL MO2 start command completed.",
            "output": result["output"], "executables": after["executables"],
            "candidates": after["candidates"],
            "verification": "MO2 executable detected in a common path." if command == "install" else "STL command exit status."}


def inspect_skyrim_mo2_instance(home: Path | None = None) -> dict:
    home = home or Path.home()
    stl = find_stl_executable(home)
    if stl is None:
        return {"ok": False, "message": "STL executable not found."}
    try:
        result = subprocess.run([str(stl), "mo2", "list-installed"], check=False,
                                capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"ok": False, "message": f"Could not list installed MO2 instances: {error}"}
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    found = any("(489830)" in line for line in output.splitlines())
    return {"ok": result.returncode == 0, "installed": found, "output": output,
            "message": "Skyrim SE MO2 instance detected." if found else "No Skyrim SE MO2 instance listed by STL."}


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
            "message": "STL command completed, but its installed-instance list does not show AppID 489830.",
            "output": result["output"], "verification": after.get("output", after.get("message"))}
