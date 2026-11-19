# Qt6 frontend prototype

This is an experimental standalone frontend for STL-Steam, implemented in Python with PySide6 (Qt 6). It is intentionally a prototype and does not yet invoke the STL Bash engine or modify Steam/game configuration.

## Run from source

Install PySide6 in a virtual environment, then run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install PySide6
python qt-ui/main.py
```

The first prototype shows the intended navigation and Skyrim-focused workflow: overview, game detection, MO2 setup, compatibility settings, and logs. Backend actions are explicitly marked as not connected until a reviewed bridge is implemented.
