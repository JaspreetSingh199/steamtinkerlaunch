#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
DESKTOP_DIR="${HOME}/.local/share/applications"
mkdir -p "${DESKTOP_DIR}"
cat > "${DESKTOP_DIR}/wyrd.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Wyrd
Comment=Manage a Linux Skyrim modding environment
Exec=bash "${APP_DIR}/qt-ui/run.sh"
Icon=applications-games
Terminal=false
Categories=Game;Utility;
EOF
chmod 644 "${DESKTOP_DIR}/wyrd.desktop"
# Remove the previous launcher installed by this project version, if present.
rm -f "${DESKTOP_DIR}/stl-steam-skyrim.desktop"
echo "Desktop launcher installed: ${DESKTOP_DIR}/wyrd.desktop"
