# Source audit: Skyrim and MO2 integration

Audit target: upstream baseline at `stl-steam` (main Bash script, 27,231 lines).

## Verified source paths

- `getGameDirFromAM` (line 14896): parses the Steam app manifest's `installdir` and resolves the game directory under the library's `steamapps/common`.
- `getGameDirFromAID` (line 14906): locates an app manifest by AppID using `listAppManifests`, then resolves its install directory.
- `listWinSteamLibraries` (line 15226): creates Windows-path mappings for Steam's root and additional libraries, using `listSteamLibraries`.
- Skyrim SE AppID 489830 is already recognized in the existing script's Vortex special-launcher handling (line 16939), with `skse64_loader.exe`; Skyrim LE AppID 72850 is also listed.
- MO2 installer functions: `getLatestMO2Ver` (17395), `dlLatestMO2` (17412), `setMO2Vars` (17452), `installMO2` (17539), and `manageMO2GInstance` (17665).
- MO2 version is temporarily pinned to 2.4.4 in upstream (17395–17410).
- MO2 installation uses an isolated Proton/Wine prefix, downloads the installer, and can use InnoExtract for unpacking. The upstream code has both portable and global instance paths.
- MO2 silent mode explicitly notes that Skyrim SE may require an executable profile such as SKSE64; the executable-profile name is overrideable (20197–20201).
- `main` starts by initializing shared memory/logging, resolves AppID/config, and performs Steam environment setup (27068 onwards).

## Installer design decisions

- The standalone installer should be independent of STL's GUI runtime and should not directly call its internal MO2 installer functions.
- Steam detection should be implemented in the installer using manifest discovery across known library folders, with a conservative fallback to parsing `libraryfolders.vdf`.
- First target is Skyrim Special Edition only (AppID 489830). Skyrim LE can be added after the SE path is tested.
- Installer must be user-local, idempotent, and refuse destructive actions. It will not edit Skyrim files, save files, MO2 profiles, mod directories, or overwrite an existing MO2.
- Before choosing a launch integration, further source audit is required to understand STL command-line entry points, Steam compatibility-tool registration, and config defaults. Do not yet modify game launch options.

## Follow-up source tracing

1. Trace `listAppManifests`, `listSteamLibraries`, and Steam root/library discovery.
2. Trace MO2 configuration variables, instance paths, and the game-specific setup menu.
3. Trace command-line invocation and compatibility-tool setup.
4. Use those findings to implement a staged installer with dry-run and verification.

## Audit caveat

This is a targeted audit of the source, not a runtime test. The installer workflow is not yet validated on a real Steam installation.

# STL-Steam launch and MO2 audit (continued)

## Installation layout verified against the main script

- Main script sets `PREFIX="/usr"` near the top of the source.
- Runtime system support files are expected under `$PREFIX/share/steamtinkerlaunch` (derived from `SYSTEMSTLCFGDIR="$PREFIX/share/${PROGNAME,,}"`).
- The installer correctly puts the executable in `PREFIX/bin/steamtinkerlaunch` and copies support data to `PREFIX/share/steamtinkerlaunch`, with PREFIX patched to the user-local STL-Steam root.
- STL user config, logs, and downloads are separate under XDG user paths; this installer does not copy or modify those.

## MO2 behavior verified

- MO2's upstream setup uses a dedicated compatibility prefix and download cache under STL's user config/data paths.
- `setMO2Vars` selects a portable instance if a game Proton prefix is present; otherwise it defaults to a global MO2 instance.
- `manageMO2GInstance` looks up the game in the internal MO2 supported-games list and creates/initializes an instance. For portable instances, it derives the instance path from the game prefix.
- Initial MO2 instance creation writes its INI and creates profile/downloads/cache/mods/overwrite paths only when the instance INI is absent.
- If an MO2 INI already exists, upstream explicitly logs that it leaves the user-created file unmodified.
- `installMO2` downloads the pinned MO2 installer and installs it through the selected Proton/Wine prefix, or uses InnoExtract when a sufficiently recent version is available.

## Design consequence

The standalone installer should not invoke MO2 installation itself or make a game-prefix decision yet. STL's normal game-launch initialization establishes the Proton environment and then its own game-menu workflow can create MO2 instances. A separate installer attempting to call these functions outside STL runtime would be brittle.

## Remaining integration questions

- Determine the exact command-line entry point that causes STL to be invoked on a game launch and the relevant Steam launch options.
- Determine which Skyrim executable (launcher, game executable, or SKSE loader) must be selected for MO2 profile configuration.
- Determine whether current STL behavior can trigger MO2 setup through a normal game launch without changing the game's Steam launch options manually.
- Verify the default Skyrim SE game entry in MO2 supported-game metadata and whether SKSE profile creation is required.

## CLI entry points discovered

- STL exposes command-line MO2 subcommands through its internal command handler: `steamtinkerlaunch mo2 download`, `mo2 install`, `mo2 start`, `mo2 list-supported`, `mo2 list-installed`, and `mo2 create-instance`.
- `mo2 install` invokes the same `installMO2` routine through its status window; `mo2 start` calls `startMO2`, which calls `prepareMO2` and then launches MO2 with the configured instance.
- `prepareMO2` is the game-aware path and accepts the AppID. It invokes `manageMO2GInstance` for numeric IDs and can pass `portable` when an MO2 instance mode has been selected.
- This audit confirms CLI capabilities, but does not yet confirm a supported Steam launch-option recipe for Skyrim. Do not add launch-option edits to the bootstrap until that is traced and tested.
