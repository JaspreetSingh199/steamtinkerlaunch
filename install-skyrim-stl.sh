#!/usr/bin/env bash
# STL-Steam Skyrim installer bootstrap (prototype)
# Safe by default: detection only unless --install is passed.

set -euo pipefail

APPID=489830
REPO="https://github.com/JaspreetSingh199/steamtinkerlaunch"
BRANCH="stl-steam"
INSTALL_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/stl-steam"
STEAM_ROOT=""
GAME_DIR=""
DRY_RUN=1

usage() {
  cat <<'EOF'
Usage: install-skyrim-stl.sh [--install] [--dry-run] [--help]

  --dry-run   Detect Steam and Skyrim only (default).
  --install   Download STL-Steam branch into a user-local directory.
  --help      Show this help.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --install) DRY_RUN=0 ;;
    --dry-run) DRY_RUN=1 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

fail() { echo "ERROR: $*" >&2; exit 1; }
note() { printf '[STL-Steam] %s\n' "$*"; }

find_steam_root() {
  local candidates=(
    "$HOME/.steam/steam"
    "$HOME/.local/share/Steam"
    "$HOME/.steam/root"
    "$HOME/.var/app/com.valvesoftware.Steam/.local/share/Steam"
  )
  for candidate in "${candidates[@]}"; do
    if [[ -d "$candidate/steamapps" ]]; then
      STEAM_ROOT="$(realpath "$candidate")"
      return 0
    fi
  done
  return 1
}

# Reads Steam's libraryfolders.vdf paths, supporting the modern nested format
# and the older path entries. The default library is included explicitly.
steam_libraries() {
  local vdf="$STEAM_ROOT/steamapps/libraryfolders.vdf"
  printf '%s\n' "$STEAM_ROOT/steamapps"
  [[ -f "$vdf" ]] || return 0
  sed -nE 's/^[[:space:]]*"path"[[:space:]]+"([^"]+)".*/\1/p' "$vdf" |
    while IFS= read -r path; do
      [[ -n "$path" && -d "$path/steamapps" ]] && printf '%s\n' "$path/steamapps"
    done
}

detect_skyrim() {
  local apps lib manifest install_dir
  apps="$(steam_libraries | sort -u)"
  while IFS= read -r lib; do
    [[ -d "$lib" ]] || continue
    manifest="$lib/appmanifest_${APPID}.acf"
    [[ -f "$manifest" ]] || continue
    install_dir="$(awk -F'"' '/"installdir"/ {print $4; exit}' "$manifest")"
    [[ -n "$install_dir" ]] || continue
    GAME_DIR="$lib/common/$install_dir"
    [[ -d "$GAME_DIR" ]] && return 0
  done <<< "$apps"
  return 1
}

for dependency in realpath awk sed sort; do
  command -v "$dependency" >/dev/null || fail "Required command '$dependency' was not found. Install it and rerun."
done

find_steam_root || fail "Steam installation not found in standard locations (native or Flatpak Steam)."
note "Steam root: $STEAM_ROOT"
detect_skyrim || fail "Skyrim Special Edition (AppID $APPID) not found in detected Steam libraries."
note "Skyrim SE detected: $GAME_DIR"
note "Detection completed successfully."

if [[ "$DRY_RUN" -eq 1 ]]; then
  note "Dry-run mode. No files were installed or changed."
  note "Run with --install to install STL-Steam into: $INSTALL_ROOT"
  exit 0
fi

command -v curl >/dev/null || fail "curl is required to download STL-Steam."
command -v tar >/dev/null || fail "tar is required to unpack STL-Steam."

tmpdir="$(mktemp -d)"
cleanup() { rm -rf "$tmpdir"; }
trap cleanup EXIT

archive="$tmpdir/stl-steam.tar.gz"
url="$REPO/archive/refs/heads/$BRANCH.tar.gz"
note "Downloading STL-Steam branch archive..."
curl --fail --location --silent --show-error "$url" -o "$archive"

# Validate archive paths before extraction. Reject absolute paths, parent traversal,
# and unexpected top-level layout to avoid extracting arbitrary files.
archive_entries="$(tar -tzf "$archive")" || fail "Downloaded archive is not a valid gzip tarball."
while IFS= read -r entry; do
  [[ -n "$entry" ]] || continue
  [[ "$entry" != /* ]] || fail "Unsafe absolute path in archive: $entry"
  IFS='/' read -r -a path_parts <<< "$entry"
  for part in "${path_parts[@]}"; do
    [[ "$part" != ".." ]] || fail "Unsafe parent traversal path in archive: $entry"
  done
  [[ "$entry" == steamtinkerlaunch-*/* || "$entry" == steamtinkerlaunch-* ]] || fail "Unexpected archive layout: $entry"
done <<< "$archive_entries"

# Symlinks and hardlinks can escape the extraction root even when archive member
# names are safe. This source installer expects a plain source tree.
archive_verbose="$(tar -tvzf "$archive")" || fail "Could not inspect archive entries."
while IFS= read -r listing; do
  [[ -n "$listing" ]] || continue
  [[ "${listing:0:1}" != "l" && "${listing:0:1}" != "h" ]] || fail "Links are not accepted in the source archive."
done <<< "$archive_verbose"

mkdir -p "$tmpdir/unpack"
tar -xzf "$archive" -C "$tmpdir/unpack"
source_dir="$(find "$tmpdir/unpack" -mindepth 1 -maxdepth 1 -type d -name 'steamtinkerlaunch-*' -print -quit)"
[[ -n "$source_dir" ]] || fail "Archive did not contain the expected source directory."
[[ -f "$source_dir/steamtinkerlaunch" ]] || fail "Main STL executable missing from archive."

if [[ -e "$INSTALL_ROOT" ]]; then
  fail "Install directory already exists: $INSTALL_ROOT. Refusing to overwrite it."
fi

# Stage the install beside the final destination so the rename is atomic and
# cannot leave a partially copied installation at INSTALL_ROOT.
install_parent="$(dirname "$INSTALL_ROOT")"
mkdir -p "$install_parent"
staging_dir="$(mktemp -d "$install_parent/.stl-steam-staging.XXXXXX")"
cleanup() { rm -rf "$tmpdir"; [[ -z "$staging_dir" ]] || rm -rf "$staging_dir"; }
trap cleanup EXIT

mkdir -p "$staging_dir/bin" "$staging_dir/share/steamtinkerlaunch"
cp "$source_dir/steamtinkerlaunch" "$staging_dir/bin/steamtinkerlaunch"
cp -a "$source_dir/collections" "$source_dir/eval" "$source_dir/guicfgs" "$source_dir/lang" "$source_dir/misc" "$staging_dir/share/steamtinkerlaunch/"
cp "$source_dir/README.md" "$staging_dir/share/doc-STL-Steam.md"
# Make the main script use the user-local prefix instead of /usr.
sed -i "s|^PREFIX=\"/usr\"|PREFIX=\"$INSTALL_ROOT\"|" "$staging_dir/bin/steamtinkerlaunch"
grep -Fq "PREFIX=\"$INSTALL_ROOT\"" "$staging_dir/bin/steamtinkerlaunch" || fail "Could not configure user-local prefix in executable."
chmod +x "$staging_dir/bin/steamtinkerlaunch"
mv "$staging_dir" "$INSTALL_ROOT"
staging_dir=""
note "STL-Steam installed to $INSTALL_ROOT"
note "This bootstrap does not alter Steam launch options or the Skyrim game directory."
note "Next setup step is still manual pending verified launch-integration work."
