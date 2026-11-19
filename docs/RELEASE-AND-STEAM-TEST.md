# GitHub Release / Steam-STL test checklist

## Release contents
Download the source archive from the GitHub Release (or the branch source ZIP). Extract it to a normal user-owned folder. This is a Python source distribution, not a compiled AppImage.

## Prerequisites
- Linux desktop session with Steam installed (native or Flatpak).
- Python 3 with `venv` and pip.
- curl, tar, awk, sed, sort, realpath for the source installer.
- Internet access on first Qt launch to install PySide6 into the project-local virtual environment.
- SteamTinkerLaunch's own runtime prerequisites. The fork's existing installation docs should be followed for distro-level dependencies.

## First run
1. Extract the archive.
2. Open a terminal in the extracted directory.
3. Run `bash install-skyrim-stl.sh` to perform detection only.
4. Run `bash qt-ui/run.sh` to open the Qt6 setup app.
5. Confirm Skyrim Special Edition (AppID 489830) is detected.
6. Review the existing STL compatibility tool, MO2 executable, and STL game config status before installing anything.

## Install STL-Steam
1. Run `bash install-skyrim-stl.sh --install`.
2. In the Qt app, use **Install as Steam Compatibility Tool** only if no existing SteamTinkerLaunch compatibility tool is present.
3. Restart Steam.
4. In Skyrim SE > Properties > Compatibility, choose SteamTinkerLaunch. Do not use `steamtinkerlaunch %command%` as the Proton game integration method.
5. Launch Skyrim once to allow STL to initialize its game config; exit after confirming STL appears.

## MO2 setup
1. Use **Install MO2 via STL** only if MO2 is not already installed.
2. Use **Create Skyrim SE MO2 instance** only when STL's list-installed output says no Skyrim instance exists.
3. Use **Enable MO2 for Skyrim SE** only if the per-game STL config is absent.
4. Launch Skyrim via Steam with STL selected. Confirm STL's MO2 GUI appears. In MO2, create/configure the Skyrim profile and choose Skyrim's executable or SKSE only when SKSE is installed and configured.

## What counts as a successful test
- Steam starts Skyrim via the STL compatibility tool.
- STL recognizes AppID 489830.
- STL shows MO2 GUI for that game.
- MO2 shows the Skyrim Special Edition instance.
- Starting the selected game executable from MO2 starts Skyrim under the game's Proton environment.

## Recovery
- Disable only an app-managed STL config using the in-app Disable action; its contents are moved to `.stl-steam-backup`.
- Restore the backup manually only after confirming the active `.conf` is absent; never overwrite an active user config.
- Steam compatibility selection is deliberately manual in this prototype; restore its previous Steam Compatibility setting yourself if needed.
