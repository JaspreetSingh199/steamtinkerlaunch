# Wyrd architecture notes: Kalium review

This document records the initial architecture review of [Kalium](https://github.com/bobbycomet/Kalium) as a reference for Wyrd. It is research and design guidance—not a commitment to copy Kalium or a claim of compatibility.

## Product boundary

Wyrd manages the Linux-side environment and integration needed to run MO2 and Skyrim through Proton. MO2 remains responsible for mod installation, profiles, load order, and its virtual filesystem behavior. Wyrd should avoid becoming a second mod manager in V1.

## Kalium concepts worth adapting

### 1. Explicit MO2 install workflow
Kalium's README and installer code separate MO2 setup from game management. The installer discovers a release, selects a suitable archive, downloads and extracts it, verifies `ModOrganizer.exe`, and then configures supporting environment pieces. Wyrd should expose each stage in Qt with status, progress, log output, cancellation, and a clear verification result.

**Wyrd adaptation:** do not report installation success based on process exit alone. Verify the expected executable, selected instance, prefix, and shortcut state independently.

### 2. Proton is an explicit model
Kalium has a Proton model that discovers Steam Proton builds and custom compatibility-tool directories, checks for Proton/Wine executables, and exposes the selected runtime. Its prefix initializer uses the Proton wrapper to initialize a prefix.

**Wyrd adaptation:** create a Proton discovery service that returns structured records (display name, path, source, architecture, Wine binary, Proton wrapper, and validation status). Do not infer architecture from the Proton folder name. Never modify Skyrim's existing prefix as a side effect of MO2 setup.

### 3. Prefix initialization and dependencies are staged
Kalium initializes prefixes with Proton, then installs dependencies and applies Wine registry settings. These operations should be individually visible and have failure boundaries.

**Wyrd adaptation:** use a dedicated MO2 prefix, with an operation journal and recovery metadata. Stage each dependency step, allow cancellation only at safe boundaries, and avoid destructive cleanup when ownership or state is uncertain.

### 4. Steam integration is separate from MO2 files
Kalium registers MO2 as a Steam non-Steam shortcut and associates it with a Proton compatibility environment. It also has logic for shortcut identity and Steam paths.

**Wyrd adaptation:** shortcut creation is a separate optional step. A successful MO2 file install should remain successful even if shortcut creation fails. Steam running-state warnings must explain how the user can safely complete the integration.

### 5. Steam library detection is multi-library aware
Kalium discovers Steam locations and library folders, reads `libraryfolders.vdf`, checks app manifests, and considers secondary library locations when locating game installations and prefixes.

**Wyrd adaptation:** use one shared Steam library discovery layer for Skyrim detection, MO2 configuration, and prefix discovery. Avoid multiple inconsistent implementations. Handle native, Flatpak, and Snap Steam only after each path model has test coverage.

### 6. MO2 repair targets MO2-owned files
Kalium includes an MO2 repair workflow that aims to repair application/plugin components without rebuilding the entire instance or touching user mod data.

**Wyrd adaptation:** define ownership scopes before implementing repair. Back up targeted files, verify the backup, stage replacements, and never remove profiles, mods, downloads, saves, or Overwrite data. Repair should be a separate feature from prefix reset.

### 7. Background task model
Kalium's task context provides progress, status, logging, and cancellation. This is a useful shape for Wyrd's Qt task system.

**Wyrd adaptation:** use worker tasks with structured events (status, progress, log, warning, result, cancellation). Keep UI responsive. Do not terminate subprocesses mid-write unless the operation supports safe cancellation; finish or roll back the current stage first.

## V1 implementation order

1. Steam discovery and library parsing (native Steam first; add Flatpak/Snap with explicit tests).
2. Proton discovery and runtime validation.
3. Dedicated MO2 prefix creation and prefix metadata.
4. MO2 download/extraction with integrity/structure checks and visible progress.
5. Dependency setup with stage-specific status, cancellation, and rollback boundaries.
6. MO2 install verification.
7. Skyrim detection and MO2 instance configuration.
8. Launch MO2 and Skyrim through a verified runtime.
9. Optional Steam shortcut registration.
10. Backup/restore, diagnostics, and repair.

## Deliberately out of V1

- ReShade
- Skyrim downgrade/backpatch tooling
- Broad game support
- Native mod manager replacement
- Wabbajack/Collections automation
- Automatic changes to existing game prefixes

## V2: modding utilities

ReShade should be an opt-in installer with clear uninstall scope and preset backup. Skyrim downgrade/backpatch support must be version-specific, validate depot/source files, back up the existing game files, and verify resulting version/hash before reporting success. It must never be bundled into ordinary MO2 setup.

## V3: native mod manager exploration

Amethyst is a research candidate, not a selected implementation. Evaluate:

- How it deploys files and handles conflicts
- Whether it provides a virtual filesystem or deployment model equivalent to MO2's needs
- Load order and plugin support
- Skyrim-specific tool integration (SKSE, LOOT, BodySlide, behavior generators)
- Existing MO2 profile migration/export
- Compatibility with large modlists and rollback
- Project activity, licensing, and maintenance health

## Reference and licensing note

Kalium is licensed under MIT (see its upstream LICENSE). If Wyrd later copies or adapts source code rather than only ideas and architectural patterns, preserve the applicable copyright and license notice, document provenance, and review each reused file before integration.

## Sources reviewed

- Kalium README: product boundary, feature inventory, setup flow, supported launchers, MO2 repair, and backpatching overview.
- `kalium/installers/mo2.py`: MO2 release retrieval, archive selection, extraction, USVFS update, dependency setup, tool integration, and managed-game setup.
- `kalium/installers/prefix_setup.py`: Proton-based prefix initialization and dependency/registry steps.
- `kalium/steam/proton.py`: Proton discovery and Wine binary checks.
- `kalium/steam/paths.py`: Steam path and library detection.
- `kalium/game_finder/steam_games.py`: appmanifest scanning and multi-library game/prefix discovery.
- `kalium/installers/mo2_game.py`: managed-game binding and MO2 game-name normalization.
- `kalium/installers/task.py`: task status, progress, logging, and cancellation interface.
- `kalium/tools/skyrim_backpatch.py`: version-specific Steam depot backpatching and backup/verification expectations.
- Kalium LICENSE: MIT License.
