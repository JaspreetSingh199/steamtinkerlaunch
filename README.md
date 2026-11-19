# STL-Steam Skyrim Setup — Qt6 desktop app

This repository contains the experimental STL-Steam fork/bootstrap and a Qt6/PySide6 helper for Skyrim Special Edition (Steam AppID 489830).

## Run from source
```bash
bash qt-ui/run.sh
```

The launcher creates `qt-ui/.venv` and installs PySide6 from `qt-ui/requirements.txt` if missing. It needs Python 3, venv/pip support, and network access on first run.

## Install a desktop menu entry
```bash
bash qt-ui/install-desktop-launcher.sh
```
Search the desktop app launcher for **STL-Steam Skyrim Setup**.

## STL-Steam source install
```bash
bash install-skyrim-stl.sh
bash install-skyrim-stl.sh --install
```
The first command is detection-only. The second installs STL-Steam into `$XDG_DATA_HOME/stl-steam` or `~/.local/share/stl-steam`. It refuses to overwrite an existing destination.

## Current capabilities
- Detects Skyrim SE in Steam libraries.
- Detects local MO2/STL state.
- Installs STL as a compatibility tool through STL's `compat add` command.
- Runs STL MO2 install/start commands behind explicit confirmation.
- Creates the Skyrim MO2 instance through STL's `mo2 create-instance 489830` command, only after checking STL's installed-instance list.
- Enables MO2 for Skyrim by creating a new STL per-game config only if missing. Current resolver: `$XDG_CONFIG_HOME/steamtinkerlaunch/gamecfgs/id/489830.conf` (default: `~/.config/steamtinkerlaunch/gamecfgs/id/489830.conf`).

## Safety and known limitations
This is not yet a fully validated game launcher. It does not rewrite Steam's localconfig.vdf or change Skyrim launch options. It does not alter Steam compatdata, game files, mods or saves. Any existing MO2 instance or per-game STL config is left alone. An app-created Skyrim config can be disabled by moving it to the provided backup name.

**Do not consider the workflow validated until Steam has been restarted, Skyrim SE selected to use SteamTinkerLaunch as its compatibility tool, and a real launch has been observed on the target machine.** The helper has not been able to test a real Steam/Proton launch from CI.

## GitHub Release
The release source archive can be downloaded and run with `bash qt-ui/run.sh`. For a GUI install, use `bash qt-ui/install-desktop-launcher.sh`. This is a source bundle, not an AppImage or self-contained binary: it needs Python 3 and installs PySide6 in a local virtual environment on first launch.
