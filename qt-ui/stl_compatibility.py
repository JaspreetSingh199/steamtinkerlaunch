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

UPSTREAM_REPO = "https://github.com/sonic2kk/steamtinkerlaunch.git"
LOCAL_INSTALL = Path("stl/prefix")

def find_stl_executable(home: Path | None = None) -> Path | None:
    home = home or Path.home()
    candidates = [
        home / "stl/prefix/steamtinkerlaunch",
        home / ".local/share/stl-steam/steamtinkerlaunch",
        home / ".local/share/stl-steam/bin/steamtinkerlaunch",
        home / ".local/share/SteamTinkerLaunch/steamtinkerlaunch",
        home / ".local/share/SteamTinkerLaunch/bin/steamtinkerlaunch",
    ]
    found = shutil.which("steamtinkerlaunch")
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    return None

def install_stl_source(home: Path | None = None, *, dry_run: bool = True) -> dict:
    """Clone upstream STL into the Protonup-Qt-compatible user-local prefix, without overwriting."""
    home = home or Path.home()
    target = home / LOCAL_INSTALL
    executable = target / "steamtinkerlaunch"
    if executable.is_file() and os.access(executable, os.X_OK):
        return {"ok": True, "dry_run": dry_run, "message": "STL source installation already exists.", "executable": str(executable)}
    if target.exists():
        return {"ok": False, "dry_run": dry_run, "message": "Install target already exists but is not a verified STL install; left untouched.", "target": str(target)}
    git = shutil.which("git")
    if not git:
        return {"ok": False, "dry_run": dry_run, "message": "Git is required to install STL from upstream."}
    if dry_run:
        return {"ok": True, "dry_run": True, "message": "Would clone upstream STL into the user-local install prefix.", "target": str(target), "executable": str(executable)}
    try:
        result = subprocess.run([git, "clone", "--depth", "1", UPSTREAM_REPO, str(target)],
                               check=False, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return {"ok": False, "dry_run": False, "message": "STL download timed out. The partial directory, if any, was left for inspection.", "target": str(target)}
    except OSError as error:
        return {"ok": False, "dry_run": False, "message": f"Could not start git clone: {error}", "target": str(target)}
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    if result.returncode != 0:
        return {"ok": False, "dry_run": False, "message": f"STL clone failed (exit {result.returncode}).", "output": output, "target": str(target)}
    if not executable.is_file():
        return {"ok": False, "dry_run": False, "message": "Clone completed but upstream executable was not found.", "output": output, "target": str(target)}
    executable.chmod(executable.stat().st_mode | 0o111)
    return {"ok": True, "dry_run": False, "message": "STL source installed.", "executable": str(executable), "output": output}

def find_steam_roots(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    candidates = [home / ".steam/root", home / ".steam/steam",
                  home / ".local/share/Steam",
                  home / ".var/app/com.valvesoftware.Steam/.local/share/Steam"]
    roots = []
    for candidate in candidates:
        if (candidate / "steamapps").is_dir():
            # Preserve the path spelling used by Steam for its compatibilitytools.d.
            if candidate not in roots:
                roots.append(candidate)
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
    """Install upstream STL locally if missing, then register it as a Steam compatibility tool."""
    home = home or Path.home()
    roots = find_steam_roots(home)
    if not roots:
        return {"ok": False, "dry_run": dry_run, "message": "No Steam root with steamapps was detected."}
    targets = compatibility_tool_targets(home)
    existing = [p for p in targets if p.exists() or p.is_symlink()]
    if existing:
        return {"ok": False, "dry_run": dry_run,
                "message": "An STL compatibility-tool directory already exists. It was left untouched.",
                "existing": [str(p) for p in existing]}
    executable = find_stl_executable(home)
    if executable is None:
        source = install_stl_source(home, dry_run=dry_run)
        if not source.get("ok"):
            return {**source, "message": "STL installation preflight failed: " + source.get("message", "")}
        if dry_run:
            return {"ok": True, "dry_run": True,
                    "message": "Would clone upstream STL into the user-local prefix, then run its compat add command.",
                    "targets": [str(p) for p in targets], "install_target": source.get("target")}
        source = install_stl_source(home, dry_run=False)
        if not source.get("ok"):
            return source
        executable = find_stl_executable(home)
        if executable is None:
            return {"ok": False, "dry_run": False,
                    "message": "STL was cloned, but executable detection failed.", "install": source}
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
    output = "\\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
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

def reset_stl_steam(home: Path | None = None, *, dry_run: bool = True) -> dict:
    """Safely reset only this app's managed source and STL compat registrations.

    The app source is moved to a timestamped backup, never recursively deleted.
    MO2/config/prefixes and Steam per-game settings are not touched.
    """
    import time
    home = home or Path.home()
    data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
    install_root = data_home / "stl-steam"
    targets = [target for target in compatibility_tool_targets(home)
               if target.exists() or target.is_symlink()]
    backup = install_root.with_name(f"stl-steam.reset-backup-{int(time.time())}")
    if backup.exists():
        return {"ok": False, "dry_run": dry_run,
                "message": "The planned backup path already exists; nothing was changed.",
                "backup": str(backup)}
    if dry_run:
        return {"ok": True, "dry_run": True,
                "message": "Preview only. The reset will move this app's source directory to a backup and remove only STL compatibility registrations owned by the detected targets.",
                "install_root": str(install_root) if install_root.exists() else None,
                "compatibility_targets": [str(path) for path in targets],
                "backup": str(backup),
                "preserved": ["Skyrim game files and saves", "MO2 installations, instances, profiles, mods and downloads",
                              "Proton prefixes", "Steam launch options and per-game configuration",
                              "STL user configuration and logs outside this app's install directory"]}
    changed = []
    try:
        # First move our own app install to a sibling backup; same filesystem for atomic rename.
        if install_root.exists() or install_root.is_symlink():
            os.rename(install_root, backup)
            changed.append(("source", backup))
        # Only remove the specifically named STL compatibility directory entries.
        # Registration is a symlink in supported upstream builds; never recursively delete a real directory.
        for target in targets:
            if target.is_symlink():
                target.unlink()
                changed.append(("compatibility_link", target))
            elif target.is_dir():
                return {"ok": False, "dry_run": False,
                        "message": "A real directory exists at a Steam compatibility target. It was left untouched because ownership cannot be proven. The app source was backed up if it had already been moved.",
                        "backup": str(backup) if backup.exists() else None,
                        "preserved_target": str(target)}
            else:
                return {"ok": False, "dry_run": False,
                        "message": "An unexpected file exists at a Steam compatibility target. It was left untouched.",
                        "backup": str(backup) if backup.exists() else None,
                        "preserved_target": str(target)}
    except OSError as error:
        return {"ok": False, "dry_run": False,
                "message": f"Reset stopped safely: {error}",
                "backup": str(backup) if backup.exists() else None,
                "changed": [str(path) for _, path in changed]}
    return {"ok": True, "dry_run": False,
            "message": "STL-Steam app source was backed up and owned compatibility links were removed. Personal game/MO2/Proton data was not touched.",
            "backup": str(backup) if backup.exists() else None,
            "removed_compatibility_links": [str(path) for kind, path in changed if kind == "compatibility_link"],
            "restart_steam": bool(targets)}


def skyrim_game_config_path(home: Path | None = None, app_id: str = "489830") -> Path:
    """Return STL's per-game config location without creating it."""
    home = home or Path.home()
    data_home = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    return data_home / "steamtinkerlaunch" / "gamecfgs" / "id" / f"{app_id}.conf"


def inspect_skyrim_mo2_config(home: Path | None = None, app_id: str = "489830") -> dict:
    path = skyrim_game_config_path(home, app_id)
    if not path.is_file():
        return {"exists": False, "path": str(path), "mo2_mode": None, "managed": False}
    try:
        text = path.read_text(errors="replace")
    except OSError as error:
        return {"exists": True, "path": str(path), "error": str(error), "managed": False}
    import re
    match = re.search(r'^\s*MO2MODE\s*=\s*"([^"]*)"', text, re.MULTILINE)
    return {"exists": True, "path": str(path),
            "mo2_mode": match.group(1) if match else None, "managed": False}


def configure_skyrim_mo2(home: Path | None = None, *, dry_run: bool = True,
                         mode: str = "gui", app_id: str = "489830") -> dict:
    """Create only a missing Skyrim STL config; preserve any existing file."""
    import tempfile
    if mode not in {"gui", "silent"}:
        return {"ok": False, "dry_run": dry_run, "message": "MO2 mode must be gui or silent."}
    state = inspect_skyrim_mo2_config(home, app_id)
    path = Path(state["path"])
    if state.get("exists"):
        return {"ok": False, "dry_run": dry_run,
                "message": "A per-game STL config already exists. It was not changed.",
                "path": str(path), "mo2_mode": state.get("mo2_mode")}
    # Refuse a symlinked config target or parent path to avoid writing outside
    # the user's STL config directory.
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent.exists()):
        return {"ok": False, "dry_run": dry_run, "message": "Symlinked config path detected; refusing to write.", "path": str(path)}
    content = f'# Managed by STL-Steam. Remove this file to disable this integration.\nMO2MODE="{mode}"\n'
    if dry_run:
        return {"ok": True, "dry_run": True, "path": str(path), "content": content,
                "message": "Would create a new Skyrim-only STL game config."}
    if path.exists():
        return {"ok": False, "dry_run": False, "message": "Config appeared before write; refusing to overwrite.", "path": str(path)}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".game.cfg.", dir=str(path.parent))
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        # Atomic no-clobber publish: hard-link the staged file to destination.
        os.link(temp_name, path)
        os.unlink(temp_name)
    except FileExistsError:
        return {"ok": False, "dry_run": False, "message": "Config appeared before write; refusing to overwrite.", "path": str(path)}
    except OSError as error:
        return {"ok": False, "dry_run": False, "message": f"Could not create Skyrim config: {error}", "path": str(path)}
    return {"ok": True, "dry_run": False, "path": str(path), "backup": None,
            "mo2_mode": mode, "message": "Created a new Skyrim-only STL MO2 config. No previous file existed."}


def remove_managed_skyrim_mo2_config(home: Path | None = None, app_id: str = "489830") -> dict:
    """Remove only a config carrying this application's ownership marker."""
    path = skyrim_game_config_path(home, app_id)
    if not path.is_file():
        return {"ok": True, "message": "No Skyrim config exists.", "path": str(path)}
    try:
        text = path.read_text(errors="replace")
    except OSError as error:
        return {"ok": False, "message": str(error), "path": str(path)}
    if not text.startswith("# Managed by STL-Steam."):
        return {"ok": False, "message": "Config is not marked as managed by STL-Steam; it was left untouched.", "path": str(path)}
    # Rename to a timestamp-independent unique backup instead of deletion.
    backup = path.with_name(path.name + ".stl-steam-backup")
    if backup.exists():
        return {"ok": False, "message": "The reversible backup already exists; refusing to replace it.", "backup": str(backup)}
    try:
        os.rename(path, backup)
    except OSError as error:
        return {"ok": False, "message": f"Could not move managed config to backup: {error}"}
    return {"ok": True, "message": "Managed config disabled and preserved as backup.", "backup": str(backup)}
