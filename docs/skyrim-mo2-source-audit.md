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
