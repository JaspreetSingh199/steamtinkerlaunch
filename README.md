# Wyrd — Skyrim Modding Environment

Wyrd is a Linux desktop application for setting up and managing a Skyrim Special Edition modding environment. The goal is a guided, reversible workflow for Mod Organizer 2 (MO2), Proton, Skyrim, and common modding tools.

> **Current status:** Experimental. The Qt6 UI is still backed by the earlier STL-Steam setup code. Wyrd's planned architecture is Kalium-inspired, with selected SteamTinkerLaunch capabilities retained as optional integrations rather than a required foundation.

## Roadmap

### V1 — Core
- MO2 installation, update, repair and verification
- Dedicated Proton environment and Proton selection
- Skyrim detection
- MO2 instance/profile management
- Skyrim launch through MO2
- SKSE detection
- One-Time Run
- Run EXE inside selected Proton
- Backup and restore
- Safe prefix repair/reset
- Environment variables and custom launch arguments
- Logs and diagnostics
- GUI-driven installation

### V2 — Modding enhancements
- ReShade setup and preset management
- Skyrim version downgrader, if safely feasible
- Additional modding utilities

### V3 — Native mod manager exploration
Investigate a native Linux mod manager as a possible complement or replacement for MO2. Amethyst is a candidate to research, not a committed implementation. Evaluate virtual filesystem/deployment behavior, conflict handling, load order, compatibility with Skyrim tools and existing MO2 workflows before choosing.

## Run from source

```bash
bash qt-ui/run.sh
```

The launcher creates `qt-ui/.venv` and installs PySide6 from `qt-ui/requirements.txt` if needed. Python 3, venv/pip support, and network access are required on first run.

## Install a desktop menu entry

```bash
bash qt-ui/install-desktop-launcher.sh
```

Search your desktop app launcher for **Wyrd**.

## Legacy STL-Steam setup

The earlier experimental STL-Steam bootstrap remains in this repository while the architecture is being migrated. Its scripts and internal paths are intentionally not renamed wholesale yet, to avoid breaking existing installs and recovery paths.

```bash
bash install-skyrim-stl.sh
bash install-skyrim-stl.sh --install
```

The first command is detection-only. The second installs the legacy STL-Steam source into its user-local destination and refuses to overwrite an existing destination.

## Safety

Wyrd should prefer user-local and reversible operations. It must not silently delete or overwrite Skyrim game files, saves, mods, MO2 instances/profiles/downloads, Proton prefixes, Steam configuration, or user STL configuration/logs. Unknown ownership is a reason to stop and ask.

## Testing

CI runs Python syntax/compile checks, unit tests, Qt offscreen smoke tests, installer integration tests, terminal-wrapper tests, and source-bundle packaging. CI cannot validate a real Steam/Proton/MO2 launch on the target Linux desktop; that remains a required real-machine test.
