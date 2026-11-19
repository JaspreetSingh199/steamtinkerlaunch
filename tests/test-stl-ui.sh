#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mock="$TMP/dialog"
cat > "$mock" <<'MOCK'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$DIALOG_ARGS"
case "$*" in
  *--menu*) printf 'selected-menu\n' ;;
  *--checklist*) printf 'item-one\nitem-two\n' ;;
  *--inputbox*) printf 'typed-value\n' ;;
  *--fselect*) printf '/tmp/selected-file\n' ;;
  *--dselect*) printf '/tmp/selected-dir\n' ;;
  *--yesno*) exit "${DIALOG_YESNO_CODE:-0}" ;;
esac
exit 0
MOCK
chmod +x "$mock"
export DIALOG_ARGS="$TMP/args"
: > "$DIALOG_ARGS"
export STL_UI_DIALOG="$mock"
source "$ROOT/misc/stl-ui.sh"

[[ "$(ui_menu Test Choose 10 50 5 option-a A option-b B)" == "selected-menu" ]]
[[ "$(ui_checklist Test Choose 10 50 5 a A on b B off)" == $'item-one\nitem-two' ]]
[[ "$(ui_input Test Enter 10 50 default)" == "typed-value" ]]
[[ "$(ui_file Test /tmp)" == "/tmp/selected-file" ]]
[[ "$(ui_directory Test /tmp)" == "/tmp/selected-dir" ]]
ui_msg Test Hello
ui_error Test Error
ui_question Test Confirm
export DIALOG_YESNO_CODE=1
if ui_question Test Decline; then
  echo "yes/no wrapper lost the dialog exit code" >&2
  exit 1
fi
grep -q -- '--menu' "$DIALOG_ARGS"
grep -q -- '--checklist' "$DIALOG_ARGS"
grep -q -- '--inputbox' "$DIALOG_ARGS"
grep -q -- '--fselect' "$DIALOG_ARGS"
grep -q -- '--dselect' "$DIALOG_ARGS"
echo "Terminal UI wrapper tests passed."
