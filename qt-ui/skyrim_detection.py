"""Read-only Steam library and Skyrim SE detection."""
from __future__ import annotations
import os
from pathlib import Path
import re

APP_ID = "489830"
STEAM_CANDIDATES = (
    ".steam/steam",
    ".local/share/Steam",
    ".steam/root",
    ".var/app/com.valvesoftware.Steam/.local/share/Steam",
)

def _parse_vdf_paths(text: str) -> list[str]:
    # Steam libraryfolders VDF: extract values associated with the "path" key.
    return [p.replace("\\\\", "\\") for p in re.findall(r'"path"\\s+"([^"]+)"', text)]

def find_steam_roots(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    roots: list[Path] = []
    for relative in STEAM_CANDIDATES:
        path = (home / relative).expanduser()
        if (path / "steamapps").is_dir():
            resolved = path.resolve()
            if resolved not in roots:
                roots.append(resolved)
    return roots

def steam_libraries(steam_root: Path) -> list[Path]:
    libraries = [steam_root / "steamapps"]
    vdf = steam_root / "steamapps" / "libraryfolders.vdf"
    if vdf.is_file():
        try:
            for raw in _parse_vdf_paths(vdf.read_text(errors="replace")):
                path = Path(raw) / "steamapps"
                if path.is_dir() and path not in libraries:
                    libraries.append(path)
        except OSError:
            pass
    return libraries

def detect_skyrim(home: Path | None = None) -> dict:
    roots = find_steam_roots(home)
    for root in roots:
        for library in steam_libraries(root):
            manifest = library / f"appmanifest_{APP_ID}.acf"
            if not manifest.is_file():
                continue
            try:
                text = manifest.read_text(errors="replace")
            except OSError:
                continue
            match = re.search(r'"installdir"\\s+"([^"]+)"', text)
            if not match:
                continue
            game = library / "common" / match.group(1)
            if game.is_dir():
                return {"found": True, "steam_root": str(root), "library": str(library), "game_dir": str(game.resolve())}
    return {"found": False, "steam_roots": [str(p) for p in roots]}

