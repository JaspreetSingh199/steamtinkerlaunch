"""Wyrd-owned MO2 installation and launch through a discovered Steam Proton build.

All paths are user-local. Existing MO2 installs and unknown prefixes are never
adopted or overwritten automatically.
"""
from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Callable

from skyrim_detection import find_steam_roots
from mo2_inspection import find_mo2_installations

APP_ID = "489830"
RELEASE_API = "https://api.github.com/repos/ModOrganizer2/modorganizer/releases/latest"
APP_DIR_NAME = "wyrd"
MO2_DIR_NAME = "mo2"
PREFIX_DIR_NAME = "compatdata/mo2-skyrim"
ProgressCallback = Callable[[int, str], None]


def _data_home(home: Path) -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")).expanduser()


def managed_paths(home: Path | None = None) -> dict[str, Path]:
    home = (home or Path.home()).expanduser()
    root = _data_home(home) / APP_DIR_NAME
    return {
        "root": root,
        "install": root / MO2_DIR_NAME,
        "prefix": root / PREFIX_DIR_NAME,
        "config": Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")).expanduser() / APP_DIR_NAME,
        "settings": Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")).expanduser() / APP_DIR_NAME / "settings.json",
    }


def _host_machine() -> str:
    return os.uname().machine.lower()


def inspect_proton_build(path: Path, host: str | None = None) -> dict:
    """Validate a Proton wrapper and its Wine ELF architecture."""
    path = Path(path).expanduser()
    wrapper = path / "proton"
    wine_candidates = (path / "files/bin/wine", path / "dist/bin/wine")
    wine = next((p for p in wine_candidates if p.is_file()), None)
    if not wrapper.is_file() or not os.access(wrapper, os.X_OK):
        return {"ok": False, "path": str(path), "message": "Proton wrapper is missing or not executable."}
    if wine is None:
        return {"ok": False, "path": str(path), "message": "Proton Wine binary was not found."}
    try:
        header = wine.read_bytes()[:20]
    except OSError as error:
        return {"ok": False, "path": str(path), "message": f"Could not inspect Proton Wine: {error}"}
    if len(header) < 20 or header[:4] != b"\x7fELF":
        return {"ok": False, "path": str(path), "message": "Proton Wine is not a valid ELF binary."}
    endian = "<" if header[5] == 1 else ">" if header[5] == 2 else None
    if endian is None:
        return {"ok": False, "path": str(path), "message": "Proton Wine has invalid ELF byte order."}
    machine_id = struct.unpack(endian + "H", header[18:20])[0]
    arch_names = {3: "x86", 40: "ARM", 62: "x86_64", 183: "AArch64"}
    architecture = arch_names.get(machine_id, f"ELF machine {machine_id}")
    host = (host or _host_machine()).lower()
    expected = {"x86_64": {62}, "amd64": {62}, "aarch64": {183}, "arm64": {183}}
    if machine_id not in expected.get(host, set()):
        return {
            "ok": False, "path": str(path), "wine": str(wine),
            "architecture": architecture, "host_architecture": host,
            "message": f"Proton Wine is {architecture}, but this system is {host}.",
        }
    return {
        "ok": True, "path": str(path.resolve()), "wrapper": str(wrapper.resolve()),
        "wine": str(wine.resolve()), "architecture": architecture,
        "host_architecture": host, "name": path.name,
        "message": f"{path.name} is compatible with {host}.",
    }


def discover_proton_builds(home: Path | None = None) -> list[dict]:
    """Discover built-in and user-installed Proton builds across Steam roots."""
    home = (home or Path.home()).expanduser()
    candidates: list[Path] = []
    for steam_root in find_steam_roots(home):
        candidates.extend((steam_root / "steamapps/common").glob("Proton*"))
        candidates.extend((steam_root / "compatibilitytools.d").iterdir()
                          if (steam_root / "compatibilitytools.d").is_dir() else [])
    extra_roots = [
        home / ".steam/root/compatibilitytools.d",
        home / ".steam/steam/compatibilitytools.d",
        home / ".local/share/Steam/compatibilitytools.d",
        Path("/usr/share/steam/compatibilitytools.d"),
        Path("/usr/lib/steam/compatibilitytools.d"),
    ]
    for root in extra_roots:
        if root.is_dir():
            try:
                candidates.extend(root.iterdir())
            except OSError:
                pass
    found: dict[str, dict] = {}
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        item = inspect_proton_build(candidate)
        if item.get("ok"):
            found[item["path"]] = item
    def sort_key(item: dict):
        name = item["name"].lower()
        # Put Experimental first, then common Proton builds, then GE/custom tools.
        priority = 0 if "experimental" in name else 1 if name.startswith("proton") else 2
        import re
        version = tuple(int(part) for part in re.findall(r"\d+", name)[-3:])
        return (priority, tuple(-v for v in version), name)
    return sorted(found.values(), key=sort_key)


def inspect_wyrd_installation(home: Path | None = None) -> dict:
    paths = managed_paths(home)
    exe = paths["install"] / "ModOrganizer.exe"
    marker = paths["install"] / ".wyrd-managed.json"
    prefix_marker = paths["prefix"] / ".wyrd-managed.json"
    installed = exe.is_file() and marker.is_file()
    metadata: dict = {}
    if installed:
        try:
            metadata = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            installed = False
        else:
            installed = installed and metadata.get("managed_by") == "Wyrd"
    prefix_ready = (paths["prefix"] / "pfx/drive_c").is_dir() and prefix_marker.is_file()
    external = [str(p) for p in find_mo2_installations(Path(home or Path.home()))]
    return {
        "installed": installed,
        "executable": str(exe) if installed else None,
        "metadata": metadata,
        "prefix_ready": prefix_ready,
        "paths": {key: str(value) for key, value in paths.items()},
        "external_installations": external,
        "message": "Wyrd-managed MO2 is installed." if installed else
                   ("An MO2 installation exists elsewhere. Wyrd will not overwrite or adopt it." if external else
                    "MO2 is not installed yet."),
    }


def _steam_root_for_game(game_path: Path, home: Path) -> Path:
    resolved_game = game_path.resolve()
    for root in find_steam_roots(home):
        try:
            resolved_game.relative_to(root.resolve())
            return root
        except ValueError:
            pass
    roots = find_steam_roots(home)
    if roots:
        return roots[0]
    raise RuntimeError("Steam was not detected. Install/launch Steam once, then refresh detection.")


def _runtime_environment(proton: Path, steam_root: Path, prefix_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update({
        "STEAM_COMPAT_CLIENT_INSTALL_PATH": str(steam_root),
        "STEAM_COMPAT_DATA_PATH": str(prefix_root),
        "SteamAppId": APP_ID,
        "SteamGameId": APP_ID,
        "STEAM_COMPAT_APP_ID": APP_ID,
        "PROTON_LOG": "0",
    })
    env.setdefault("PROTON_NO_ESYNC", "0")
    return env


def _run_proton(proton: Path, steam_root: Path, prefix_root: Path,
                arguments: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
    command = [str(proton / "proton"), "run", *arguments]
    env = _runtime_environment(proton, steam_root, prefix_root)
    try:
        return subprocess.run(command, env=env, cwd=str(proton), check=False,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"Proton command timed out: {' '.join(arguments)}") from error
    except OSError as error:
        raise RuntimeError(f"Could not start Proton: {error}") from error


def _prefix_ready(prefix_root: Path) -> bool:
    return (prefix_root / "pfx/drive_c").is_dir()


def _initialize_prefix(proton: Path, steam_root: Path, prefix_root: Path,
                       game_path: Path, callback: ProgressCallback | None = None) -> None:
    marker = prefix_root / ".wyrd-managed.json"
    if prefix_root.exists() and not marker.is_file():
        raise RuntimeError(
            f"The intended MO2 prefix already exists but is not marked as Wyrd-managed: {prefix_root}. "
            "It was left untouched."
        )
    if not prefix_root.exists():
        prefix_root.mkdir(parents=True, exist_ok=False)
        marker.write_text(json.dumps({
            "managed_by": "Wyrd", "created": datetime.now(timezone.utc).isoformat(),
            "game_app_id": APP_ID, "proton": str(proton.resolve()),
        }, indent=2), encoding="utf-8")
    if callback:
        callback(25, "Initializing Wyrd's dedicated Proton prefix…")
    result = _run_proton(proton, steam_root, prefix_root, ["wineboot", "-u"], timeout=900)
    if result.returncode != 0 or not _prefix_ready(prefix_root):
        details = (result.stdout + "\n" + result.stderr).strip()
        raise RuntimeError("Proton could not initialize the dedicated MO2 prefix." +
                           ("\n" + details[-4000:] if details else ""))
    # Register the detected game path in this MO2-only prefix. Skyrim's real
    # Steam prefix and game files are not changed.
    normalized = "Z:" + str(game_path.resolve()).replace("/", "\\")
    escaped = normalized.replace("\\", "\\\\")
    registry = (
        "Windows Registry Editor Version 5.00\n\n"
        "[HKEY_LOCAL_MACHINE\\Software\\Bethesda Softworks\\Skyrim Special Edition]\n"
        f'"Installed Path"="{escaped}"\n'
    )
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".reg", delete=False) as handle:
        handle.write(registry)
        reg_path = Path(handle.name)
    try:
        if callback:
            callback(35, "Registering the detected Skyrim location in Wyrd's prefix…")
        imported = _run_proton(proton, steam_root, prefix_root,
                               ["regedit", "/S", str(reg_path)], timeout=120)
        if imported.returncode != 0:
            details = (imported.stdout + "\n" + imported.stderr).strip()
            raise RuntimeError("Could not register Skyrim in Wyrd's MO2 prefix." +
                               ("\n" + details[-3000:] if details else ""))
    finally:
        reg_path.unlink(missing_ok=True)


def _latest_mo2_archive() -> tuple[str, str, str]:
    request = urllib.request.Request(RELEASE_API, headers={"User-Agent": "Wyrd-MO2-Installer"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            release = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        raise RuntimeError(f"Could not retrieve the latest MO2 release: {error}") from error
    excluded = ("pdbs", "src", "uibase", "commits")
    assets = [
        asset for asset in release.get("assets", [])
        if asset.get("name", "").startswith("Mod.Organizer-")
        and asset.get("name", "").endswith(".7z")
        and not any(token in asset.get("name", "").lower() for token in excluded)
        and asset.get("browser_download_url")
    ]
    if len(assets) != 1:
        raise RuntimeError("The latest MO2 release did not expose exactly one standard .7z archive.")
    asset = assets[0]
    return release.get("tag_name", "unknown"), asset["name"], asset["browser_download_url"]


def _download_archive(url: str, destination: Path,
                      callback: ProgressCallback | None = None) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Wyrd-MO2-Installer"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as out:
            total = int(response.headers.get("Content-Length", "0") or 0)
            downloaded = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                if callback:
                    percent = 40 + (int(downloaded * 45 / total) if total else 0)
                    callback(min(percent, 85), f"Downloading MO2… {downloaded // (1024 * 1024)} MiB")
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def _validate_archive_members(names: list[str]) -> None:
    for name in names:
        normalized = name.replace("\\", "/")
        path = Path(normalized)
        if path.is_absolute() or PureWindowsPath(normalized).is_absolute() or any(part == ".." for part in path.parts):
            raise RuntimeError(f"Unsafe path in MO2 archive: {name}")


def _extract_mo2(archive: Path, stage: Path, callback: ProgressCallback | None = None) -> Path:
    try:
        import py7zr
    except ImportError as error:
        raise RuntimeError("The 7z extraction component is missing. Re-run Wyrd's GUI launcher to install its dependencies.") from error
    if callback:
        callback(87, "Extracting the official MO2 archive…")
    stage.mkdir(parents=True, exist_ok=True)
    with py7zr.SevenZipFile(archive, mode="r") as bundle:
        _validate_archive_members(bundle.getnames())
        bundle.extractall(path=stage)
    executables = list(stage.rglob("ModOrganizer.exe"))
    if len(executables) != 1:
        raise RuntimeError("The MO2 archive did not contain exactly one ModOrganizer.exe.")
    return executables[0].parent


def install_mo2_environment(proton_path: Path, game_path: Path,
                            home: Path | None = None,
                            callback: ProgressCallback | None = None) -> dict:
    """Install the current official MO2 archive and initialize its isolated Proton prefix."""
    home = (home or Path.home()).expanduser()
    proton_path = Path(proton_path).expanduser().resolve()
    game_path = Path(game_path).expanduser().resolve()
    validation = inspect_proton_build(proton_path)
    if not validation.get("ok"):
        raise RuntimeError(validation.get("message", "Selected Proton build is invalid."))
    if not game_path.is_dir():
        raise RuntimeError(f"Detected Skyrim directory is no longer available: {game_path}")
    steam_root = _steam_root_for_game(game_path, home)
    paths = managed_paths(home)
    paths["root"].mkdir(parents=True, exist_ok=True)
    install_dir, prefix_root = paths["install"], paths["prefix"]
    if install_dir.exists():
        state = inspect_wyrd_installation(home)
        if state.get("installed"):
            if not state.get("prefix_ready"):
                if callback:
                    callback(10, "Repairing Wyrd's incomplete Proton prefix…")
                _initialize_prefix(proton_path, steam_root, prefix_root, game_path, callback)
                return {
                    "ok": True, "already_installed": True,
                    "executable": state.get("executable"), "version": state.get("metadata", {}).get("version", "unknown"),
                    "proton": str(proton_path), "prefix": str(prefix_root),
                    "game_path": str(game_path),
                    "message": "The Wyrd Proton prefix was initialized and the existing MO2 installation was verified.",
                }
            return {"ok": True, "already_installed": True, **state}
        raise RuntimeError(f"MO2 install target already exists but is not a verified Wyrd installation: {install_dir}. It was left untouched.")
    if callback:
        callback(5, "Checking the official MO2 release…")
    version, archive_name, url = _latest_mo2_archive()
    if callback:
        callback(15, f"Preparing MO2 {version}…")
    _initialize_prefix(proton_path, steam_root, prefix_root, game_path, callback)
    staging_root = paths["root"] / "staging"
    staging_root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="mo2-", dir=staging_root))
    archive = stage / archive_name
    try:
        _download_archive(url, archive, callback)
        extracted = _extract_mo2(archive, stage / "extracted", callback)
        if callback:
            callback(94, "Verifying the MO2 application files…")
        if not (extracted / "ModOrganizer.exe").is_file():
            raise RuntimeError("MO2 verification failed: ModOrganizer.exe is missing.")
        if extracted != stage / "extracted":
            # The archive sometimes contains a wrapper directory; move its
            # actual application root into the canonical Wyrd location.
            content_root = extracted
        else:
            content_root = extracted
        (content_root / ".wyrd-managed.json").write_text(json.dumps({
            "managed_by": "Wyrd", "version": version,
            "installed": datetime.now(timezone.utc).isoformat(),
            "proton": str(proton_path), "steam_root": str(steam_root),
            "game_app_id": APP_ID, "game_path": str(game_path),
            "prefix": str(prefix_root),
        }, indent=2), encoding="utf-8")
        if install_dir.exists():
            raise RuntimeError(f"Install target appeared during setup: {install_dir}. Existing files were not changed.")
        os.replace(content_root, install_dir)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    if callback:
        callback(100, "MO2 installed and verified. You can launch it now.")
    return {
        "ok": True, "already_installed": False,
        "executable": str(install_dir / "ModOrganizer.exe"),
        "version": version, "proton": str(proton_path),
        "prefix": str(prefix_root), "game_path": str(game_path),
        "message": f"MO2 {version} installed and verified in Wyrd's dedicated Proton environment.",
    }


def launch_mo2(home: Path | None = None, pick_instance: bool = False) -> dict:
    """Launch MO2 visibly through its configured Proton build."""
    home = (home or Path.home()).expanduser()
    state = inspect_wyrd_installation(home)
    if not state.get("installed"):
        return {"ok": False, "message": "Wyrd-managed MO2 is not installed yet."}
    metadata = state.get("metadata", {})
    proton_path = Path(metadata.get("proton", ""))
    game_path = Path(metadata.get("game_path", ""))
    paths = managed_paths(home)
    if not proton_path.is_dir() or not game_path.is_dir() or not _prefix_ready(paths["prefix"]):
        return {"ok": False, "message": "The saved Proton runtime, Skyrim directory, or MO2 prefix is missing. Refresh detection and repair the setup before launching."}
    validation = inspect_proton_build(proton_path)
    if not validation.get("ok"):
        return {"ok": False, "message": validation.get("message", "Selected Proton build is no longer valid.")}
    executable = paths["install"] / "ModOrganizer.exe"
    arguments = [str(executable)]
    if pick_instance:
        arguments.append("--pick")
    env = _runtime_environment(proton_path, Path(metadata["steam_root"]), paths["prefix"])
    try:
        process = subprocess.Popen(
            [str(proton_path / "proton"), "run", *arguments],
            cwd=str(paths["install"]), env=env, stdin=None, stdout=None, stderr=None,
            start_new_session=True,
        )
    except OSError as error:
        return {"ok": False, "message": f"Could not launch MO2 through Proton: {error}"}
    return {"ok": True, "pid": process.pid,
            "message": "MO2 launched through Wyrd's dedicated Proton prefix."}


def write_settings(home: Path | None, proton_path: Path, game_path: Path) -> None:
    paths = managed_paths(home)
    paths["config"].mkdir(parents=True, exist_ok=True)
    temporary = paths["settings"].with_suffix(".tmp")
    temporary.write_text(json.dumps({
        "proton": str(proton_path.resolve()), "game_path": str(game_path.resolve()),
        "updated": datetime.now(timezone.utc).isoformat(),
    }, indent=2), encoding="utf-8")
    os.replace(temporary, paths["settings"])
