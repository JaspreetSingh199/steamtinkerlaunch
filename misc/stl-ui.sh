#!/usr/bin/env bash
# STL terminal UI compatibility layer.
# Source this file; stdout is reserved for selected/input values.

STL_UI_DIALOG="${STL_UI_DIALOG:-dialog}"

stl_ui_require() {
  command -v "$STL_UI_DIALOG" >/dev/null 2>&1 || {
    printf 'STL UI requires dialog (ncurses). Install the dialog package and retry.\n' >&2
    return 127
  }
}

ui_msg() {
  local title="${1:-SteamTinkerLaunch}" message="${2:-}"
  stl_ui_require || return
  "$STL_UI_DIALOG" --title "$title" --msgbox "$message" 10 70
}

ui_error() {
  local title="${1:-Error}" message="${2:-}"
  stl_ui_require || return
  "$STL_UI_DIALOG" --title "$title" --msgbox "$message" 10 70 >&2
}

ui_question() {
  local title="${1:-SteamTinkerLaunch}" message="${2:-}"
  stl_ui_require || return
  "$STL_UI_DIALOG" --title "$title" --yesno "$message" 10 70
}

ui_menu() {
  local title="${1:-Menu}" prompt="${2:-Select an option}" height="${3:-20}" width="${4:-70}" menu_height="${5:-10}"
  shift 5 || true
  stl_ui_require || return
  "$STL_UI_DIALOG" --stdout --title "$title" --menu "$prompt" "$height" "$width" "$menu_height" "$@"
}

ui_checklist() {
  local title="${1:-Selection}" prompt="${2:-Select items}" height="${3:-20}" width="${4:-70}" list_height="${5:-10}"
  shift 5 || true
  stl_ui_require || return
  "$STL_UI_DIALOG" --stdout --separate-output --title "$title" --checklist "$prompt" "$height" "$width" "$list_height" "$@"
}

ui_input() {
  local title="${1:-Input}" prompt="${2:-Enter value}" height="${3:-10}" width="${4:-70}" initial="${5:-}"
  stl_ui_require || return
  "$STL_UI_DIALOG" --stdout --title "$title" --inputbox "$prompt" "$height" "$width" "$initial"
}

ui_file() {
  local title="${1:-Select file}" initial="${2:-}"
  stl_ui_require || return
  "$STL_UI_DIALOG" --stdout --title "$title" --fselect "$initial" 15 70
}

ui_directory() {
  local title="${1:-Select directory}" initial="${2:-}"
  stl_ui_require || return
  "$STL_UI_DIALOG" --stdout --title "$title" --dselect "$initial" 15 70
}

ui_gauge() {
  local title="${1:-Progress}" message="${2:-Working...}" height="${3:-8}" width="${4:-60}"
  stl_ui_require || return
  # Dialog's gauge consumes percentage values on stdin; keep its output off stdout.
  "$STL_UI_DIALOG" --title "$title" --gauge "$message" "$height" "$width" 0
}
