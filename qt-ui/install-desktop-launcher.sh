#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
DESKTOP_DIR="${HOME}/.local/share/applications"
mkdir -p "${DESKTOP_DIR}"
cat > "${DESKTOP_DIR}/stl-steam-skyrim.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=STL-Steam Skyrim Setup
Comment=Detect and set up Skyrim Special Edition for STL-Steam
Exec=bash "${APP_DIR}/qt-ui/run.sh"
Icon=applications-games
Terminal=false
Categories=Game;Utility;
EOF
chmod 644 "${DESKTOP_DIR}/stl-steam-skyrim.desktop"
echo "Desktop launcher installed: ${DESKTOP_DIR}/stl-steam-skyrim.desktop"
