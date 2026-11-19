# Wyrd Qt6 desktop application

Run the GUI:

~~~bash
bash qt-ui/run.sh
~~~

Install a desktop menu entry:

~~~bash
bash qt-ui/install-desktop-launcher.sh
~~~

The active setup flow is entirely in Qt6. It detects Skyrim SE and compatible Steam Proton builds, installs the standard official MO2 7z release into Wyrd's user-local application folder, initializes a dedicated Proton prefix, and launches MO2 through that runtime.

The GUI requires Python 3, venv/pip support, and network access on first run. The project virtual environment installs PySide6 and py7zr automatically.

Wyrd does not call SteamTinkerLaunch to install or launch MO2. Existing MO2 installations outside Wyrd's managed location are detected where possible and are left untouched. The game path is registered only in Wyrd's dedicated prefix. No Steam launch options, Skyrim files, saves, game prefix, or existing MO2 instance are edited.

On first MO2 launch, create a Skyrim Special Edition instance in MO2's own instance picker. Select Skyrim or SKSE in MO2's executable dropdown and press Run to launch through MO2's virtual filesystem.
