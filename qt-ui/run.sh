#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 -m venv "${SCRIPT_DIR}/.venv" 2>/dev/null || true
if [[ ! -x "${SCRIPT_DIR}/.venv/bin/python" ]]; then
  echo "Python 3 is required." >&2
  exit 1
fi
if ! "${SCRIPT_DIR}/.venv/bin/python" -c 'import PySide6' >/dev/null 2>&1; then
  "${SCRIPT_DIR}/.venv/bin/python" -m pip install -r "${SCRIPT_DIR}/requirements.txt"
fi
exec "${SCRIPT_DIR}/.venv/bin/python" "${SCRIPT_DIR}/main.py"
