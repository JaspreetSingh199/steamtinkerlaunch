#!/usr/bin/env bash
# Integration tests for install-skyrim-stl.sh using isolated fake Steam layouts.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLER="$SCRIPT_DIR/install-skyrim-stl.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }
run_installer() {
  HOME="$TMP/home" XDG_DATA_HOME="$TMP/data" bash "$INSTALLER" "$@"
}
mkdir -p "$TMP/home"

# 1. No Steam: must fail with a useful message.
if output="$(run_installer --dry-run 2>&1)"; then
  fail "installer unexpectedly succeeded without Steam"
fi
grep -q "Steam installation not found" <<<"$output" || fail "missing no-Steam error"
pass "no-Steam detection"

# 2. Steam exists, but Skyrim is not installed.
steam="$TMP/home/.local/share/Steam"
mkdir -p "$steam/steamapps"
if output="$(run_installer --dry-run 2>&1)"; then
  fail "installer unexpectedly succeeded without Skyrim"
fi
grep -q "Skyrim Special Edition" <<<"$output" || fail "missing no-Skyrim error"
pass "missing Skyrim detection"

# 3. Skyrim in the default library.
game="$steam/steamapps/common/Skyrim Special Edition"
mkdir -p "$game"
cat > "$steam/steamapps/appmanifest_489830.acf" <<'MANIFEST'
"AppState"
{
  "appid" "489830"
  "installdir" "Skyrim Special Edition"
}
MANIFEST
output="$(run_installer --dry-run 2>&1)" || fail "default-library detection failed"
grep -q "$game" <<<"$output" || fail "default library game path not reported"
grep -q "Dry-run mode" <<<"$output" || fail "dry-run summary missing"
pass "default Steam library detection"

# 4. Skyrim in an alternate library from libraryfolders.vdf.
rm -rf "$game" "$steam/steamapps/appmanifest_489830.acf"
alt="$TMP/alternate-library"
mkdir -p "$alt/steamapps/common/Skyrim Special Edition"
cat > "$steam/steamapps/libraryfolders.vdf" <<VDF
"libraryfolders"
{
  "0"
  {
    "path" "$steam"
    "apps"
    {
    }
  }
  "1"
  {
    "path" "$alt"
    "apps"
    {
      "489830" "1"
    }
  }
}
VDF
cat > "$alt/steamapps/appmanifest_489830.acf" <<'MANIFEST'
"AppState"
{
  "appid" "489830"
  "installdir" "Skyrim Special Edition"
}
MANIFEST
output="$(run_installer --dry-run 2>&1)" || fail "alternate-library detection failed"
grep -q "$alt/steamapps/common/Skyrim Special Edition" <<<"$output" || fail "alternate game path not reported"
pass "alternate Steam library detection"

echo "All installer detection tests passed."
