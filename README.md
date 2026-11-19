# Wyrd — Skyrim Modding Environment

Wyrd is a **Qt6 desktop GUI** for preparing a Skyrim Special Edition + Mod Organizer 2 environment on Linux. Its immediate job is deliberately small:

1. Detect Skyrim Special Edition in the user's Steam libraries.
2. Detect installed Proton builds and reject incompatible Wine architectures.
3. Download and verify the official MO2 release.
4. Initialize a dedicated Proton prefix owned by Wyrd.
5. Launch MO2 through that Proton runtime so MO2 can launch Skyrim through its virtual filesystem.

Wyrd does not use SteamTinkerLaunch to install or launch MO2. Legacy STL files remain in the repository during migration, but the active Qt6 setup flow is independent of them.

## Run Wyrd

~~~bash
bash qt-ui/run.sh
~~~

The launcher creates a local Python virtual environment and installs the Qt6 GUI and 7z extraction dependency on first run. You can also install a desktop menu entry:

~~~bash
bash qt-ui/install-desktop-launcher.sh
~~~

Search your desktop app launcher for **Wyrd**. All setup, progress, status, and launch actions are inside the Qt GUI. The shell command above only starts the desktop application.

## First-run workflow

- Install and launch Skyrim Special Edition through Steam.
- Install a current Proton build through Steam's Compatibility settings or ProtonUp-Qt. Wyrd discovers Steam's built-in and user-installed Proton directories.
- Open Wyrd, confirm the detected game and selected Proton build, and press **Install MO2**.
- Wyrd downloads the standard 7z archive from the official [Mod Organizer 2 releases](https://github.com/ModOrganizer2/modorganizer/releases), validates the archive paths, extracts it into Wyrd's user-local application folder, and verifies ModOrganizer.exe.
- Wyrd creates a separate prefix under ~/.local/share/wyrd/compatdata/mo2-skyrim. The detected Skyrim install path is registered only in this Wyrd prefix; the Skyrim game directory and Steam's own compatibility prefix are not modified.
- Press **Launch MO2**. On the first launch, create a new MO2 instance and select **Skyrim Special Edition**. In MO2, select Skyrim or SKSE in the executable dropdown and press **Run**. MO2 then launches the game through its mod virtual filesystem.

Wyrd leaves any existing MO2 installation untouched. It will not adopt or overwrite an unknown directory at its managed install/prefix paths. If an interrupted setup leaves a Wyrd-managed prefix incomplete, the GUI offers a prefix repair by rerunning Proton initialization; it does not delete the prefix.

## Current scope and known limitation

The current milestone is the core Skyrim SE → Proton → MO2 → game path. The first MO2 instance is created in MO2's own instance picker; Wyrd does not yet automate instance creation, SKSE setup, profile management, or a dedicated one-click game-launch action. Those come only after the basic desktop workflow has been tested on a real Steam/Proton system.

CI can validate Python logic, archive/path safety, Proton architecture detection, and Qt widget behavior. CI cannot prove a real MO2 window or Skyrim game launch on the target Linux desktop; that final verification must happen on a machine with Steam, Skyrim, and Proton installed.

## Testing

CI runs Python compile checks, unit tests, Qt offscreen smoke tests, legacy installer checks, and source-bundle packaging. Wyrd's active setup GUI is Qt6; there is no terminal UI workflow for MO2 setup.
