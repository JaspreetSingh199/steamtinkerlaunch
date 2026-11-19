# STL-Steam project plan

## Target

Build a Skyrim-focused installer that detects an existing Steam installation and Skyrim game, installs STL-Steam in a user-owned location, and prepares a Mod Organizer 2 workflow.

## Supported initial detection

- Skyrim Special Edition: Steam AppID 489830
- Skyrim Legendary Edition: Steam AppID 72850 (optional; include only after the first edition is verified)

Detection should inspect Steam library manifests rather than assume a single Steam library path.

## Installer safety requirements

- Do not modify Skyrim game files.
- Do not overwrite an existing MO2 installation, profile, mods, saves, or downloads.
- Do not install system packages silently or invoke sudo without an explicit user prompt.
- Make repeat runs safe (idempotent).
- Use a user-local installation by default.
- Back up any Steam configuration file before modifying it.
- Provide a dry-run mode and clear summary.
- Fail with actionable errors; do not continue after partial prerequisite failures.

## Milestones

1. Source audit: trace startup, game detection, compatibility-tool install layout, MO2 install and configuration paths.
2. Feature inventory and dependency map: identify Vortex, VR, Geo-11 and related UI/config references before removal.
3. STL-Steam baseline: keep upstream launch behavior intact; add project identity and isolated defaults only after the source audit.
4. Skyrim workflow: determine the least invasive supported way to launch Skyrim through STL-Steam and trigger MO2 setup.
5. Installer: implement a standalone shell installer that detects Steam libraries and Skyrim, installs STL-Steam, configures the Skyrim workflow, and verifies it.
6. Test: static checks, dry-run against fake Steam libraries, repeat-run tests, and then manual testing on Pauline.

## Current source findings

- Main executable is a Bash script named `steamtinkerlaunch`.
- The Makefile installs the executable into `PREFIX/bin` and support data into `PREFIX/share/steamtinkerlaunch`.
- MO2 installation/configuration functions exist in the main script. The current source uses MO2 2.4.4 and supports portable/global instances.
- Skyrim Special Edition AppID 489830 and Skyrim AppID 72850 appear in the existing Vortex special-launcher handling.
- Steam library/AppID detection and compatibility-tool paths are already represented in the source; the installer should reuse the stable Steam library detection concepts, but remain independent and conservative.

## Current status

- Fork: `JaspreetSingh199/steamtinkerlaunch`
- Working branch: `stl-steam`
- Installer prototype is committed and CI-tested with mocked fixtures. Coverage includes missing Steam, missing Skyrim, default library, alternate library, Flatpak Steam, staged install layout, local PREFIX configuration, and refusal to overwrite.
- CI performs Bash syntax checks and integration tests on pushes to `stl-steam`.
- Installer is dry-run by default and uses a staging directory before final placement.
- Source audit confirmed Skyrim SE is supported by STL's MO2 metadata (AppID 489830).
- Source audit confirmed MO2 is disabled by default unless game config enables it; normal launch calls `checkMO2`, which can set up MO2 when enabled.
- Steam launch-option integration and safe game-config setup are not yet implemented; runtime validation remains pending.
