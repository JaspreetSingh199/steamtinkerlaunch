# Skyrim STL-Steam bootstrap

This is an experimental user-local installer for the STL-Steam fork. It currently
only detects Skyrim Special Edition and installs the STL-Steam source tree into
`$XDG_DATA_HOME/stl-steam` (or `~/.local/share/stl-steam` when XDG_DATA_HOME
is unset).

## Current behavior

- Supports native Steam in common locations and Flatpak Steam.
- Detects Skyrim Special Edition (Steam AppID 489830) in the default or
  additional Steam libraries.
- Dry-run is the default. It does not install or modify files.
- `--install` downloads the branch archive, validates member paths and rejects
  links, stages files in the destination parent, then moves the staged tree into
  place.
- Refuses to overwrite an existing STL-Steam install.
- Does not modify Steam launch options, Skyrim files, saves, mods, or MO2
  instances.

## Detection-only run

```bash
bash install-skyrim-stl.sh
```

## Install STL-Steam

```bash
bash install-skyrim-stl.sh --install
```

## Test the bootstrap

```bash
bash tests/test-install-skyrim-stl.sh
```

GitHub Actions runs Bash syntax checks and these fixture-based tests on pushes to
`stl-steam`.

## Not yet ready for game setup

MO2 integration is still being traced. Do not treat this bootstrap as a complete
Skyrim modding setup until a verified launch/configuration path is implemented
and tested. The next milestone is an explicit, reversible Skyrim setup step that
does not overwrite an existing per-game STL config.
