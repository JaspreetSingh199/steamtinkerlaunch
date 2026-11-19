#!/usr/bin/env python3
"""Qt 6 desktop shell for STL-Steam's Skyrim setup."""
from __future__ import annotations

import sys
from pathlib import Path
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import (
    QApplication, QFrame, QLabel, QListWidget, QMainWindow, QPushButton,
    QStackedWidget, QVBoxLayout, QHBoxLayout, QWidget, QPlainTextEdit, QMessageBox,
)
from skyrim_detection import detect_skyrim
from mo2_inspection import inspect_mo2, inspect_stl_installation
from stl_compatibility import install_compatibility_tool, inspect_compatibility_tool
from mo2_setup import run_mo2_command, create_skyrim_mo2_instance, inspect_skyrim_mo2_instance
from stl_compatibility import configure_skyrim_mo2, inspect_skyrim_mo2_config, remove_managed_skyrim_mo2_config

STYLE = """
QWidget { background: #15171b; color: #e5e7eb; font-size: 14px; }
QListWidget { background: #1d2026; border: 0; padding: 8px; }
QListWidget::item { padding: 12px; border-radius: 8px; }
QListWidget::item:selected { background: #2d3748; color: #fff; }
QFrame#card { background: #20232a; border: 1px solid #343943; border-radius: 12px; }
QLabel#heading { font-size: 26px; font-weight: 650; }
QLabel#muted { color: #9ca3af; }
QPushButton { background: #303744; border: 1px solid #46505f; border-radius: 8px; padding: 10px 16px; }
QPushButton:hover { background: #3a4555; }
QPushButton:disabled { color: #8b929c; background: #262a31; }
"""

def card(title: str, description: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 16, 16, 16)
    title_label = QLabel(title)
    title_label.setStyleSheet("font-size: 17px; font-weight: bold;")
    detail = QLabel(description)
    detail.setObjectName("muted")
    detail.setWordWrap(True)
    layout.addWidget(title_label)
    layout.addWidget(detail)
    return frame

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("STL-Steam — Skyrim Setup")
        self.resize(1050, 680)
        root = QWidget()
        row = QHBoxLayout(root)
        row.setContentsMargins(14, 14, 14, 14)
        row.setSpacing(12)

        self.nav = QListWidget()
        self.nav.setFixedWidth(210)
        self.nav.addItems(["Overview", "Game Detection", "MO2 Setup", "Compatibility", "Logs"])
        self.nav.setCurrentRow(0)
        self.pages = QStackedWidget()
        self.overview_page = self.overview()
        self.detection_page = self.detection()
        self.pages.addWidget(self.overview_page)
        self.pages.addWidget(self.detection_page)
        self.mo2_page = self.mo2_setup()
        self.compatibility_page = self.compatibility()
        self.logs_page = self.logs()
        self.pages.addWidget(self.mo2_page)
        self.pages.addWidget(self.compatibility_page)
        self.pages.addWidget(self.logs_page)
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        row.addWidget(self.nav)
        row.addWidget(self.pages, 1)
        self.setCentralWidget(root)
        self.refresh_detection()
        self.refresh_mo2()
        self.refresh_stl()
        self.refresh_skyrim_mo2_config()
        self.refresh_skyrim_instance()

    def overview(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        heading = QLabel("Skyrim Setup")
        heading.setObjectName("heading")
        subtitle = QLabel("A guided, reversible STL-Steam setup")
        subtitle.setObjectName("muted")
        layout.addWidget(heading)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        self.game_summary = card("Skyrim detection", "Checking Steam libraries…")
        layout.addWidget(self.game_summary)
        layout.addWidget(card("STL-Steam", "The installer will be staged and verified before setup actions are enabled."))
        layout.addWidget(card("Mod Organizer 2", "Existing MO2 installations and instances will be preserved."))
        layout.addStretch(1)
        note = QLabel("Read-only detection is enabled. Steam launch options and the game prefix are not modified.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        return page

    def detection(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        heading = QLabel("Game Detection")
        heading.setObjectName("heading")
        explanation = QLabel("Searches Steam's standard locations and libraryfolders.vdf. This is read-only.")
        explanation.setObjectName("muted")
        explanation.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(explanation)
        self.detect_result = card("Status", "Checking…")
        layout.addWidget(self.detect_result)
        refresh = QPushButton("Refresh detection")
        refresh.clicked.connect(self.refresh_detection)
        layout.addWidget(refresh)
        layout.addStretch(1)
        return page

    def mo2_setup(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        heading = QLabel("MO2 Setup")
        heading.setObjectName("heading")
        intro = QLabel("Read-only discovery of existing Mod Organizer 2 installs. No instance, prefix, save, or mod files are changed.")
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(intro)
        self.mo2_result = card("Mod Organizer 2", "Checking known locations…")
        layout.addWidget(self.mo2_result)
        refresh = QPushButton("Refresh MO2 detection")
        refresh.clicked.connect(self.refresh_mo2)
        layout.addWidget(refresh)
        install = QPushButton("Install MO2 via STL")
        install.clicked.connect(lambda: self.run_mo2_action("install"))
        layout.addWidget(install)
        start = QPushButton("Start MO2 standalone")
        start.clicked.connect(lambda: self.run_mo2_action("start"))
        layout.addWidget(start)
        configure = QPushButton("Enable MO2 for Skyrim SE")
        configure.clicked.connect(self.enable_skyrim_mo2)
        layout.addWidget(configure)
        disable = QPushButton("Disable managed Skyrim MO2 config")
        disable.clicked.connect(self.disable_skyrim_mo2)
        layout.addWidget(disable)
        instance = QPushButton("Create Skyrim SE MO2 instance")
        instance.clicked.connect(self.create_skyrim_instance)
        layout.addWidget(instance)
        verify_instance = QPushButton("Check Skyrim MO2 instance")
        verify_instance.clicked.connect(self.refresh_skyrim_instance)
        layout.addWidget(verify_instance)
        self.instance_status = QLabel("Skyrim instance status not checked yet.")
        self.instance_status.setObjectName("muted")
        self.instance_status.setWordWrap(True)
        layout.addWidget(self.instance_status)
        self.skyrim_mo2_status = QLabel("Checking Skyrim per-game MO2 configuration…")
        self.skyrim_mo2_status.setObjectName("muted")
        self.skyrim_mo2_status.setWordWrap(True)
        layout.addWidget(self.skyrim_mo2_status)
        layout.addStretch(1)
        return page

    def refresh_mo2(self) -> None:
        result = inspect_mo2()
        if result["found"]:
            detail = "Existing installation(s):\n" + "\n".join(result["installations"]) + "\n\nNo changes made."
            status = "MO2 installation found"
        else:
            detail = "No MO2 installation found in the common locations.\n\nNo folders were created and no existing data was changed."
            status = "MO2 not detected"
        self.mo2_result = self._replace_card(self.mo2_page, self.mo2_result, card(status, detail))
        self._append_log("MO2 discovery: " + status + " (common paths only; STL MO2COMPDATA may be customized)")

    def refresh_skyrim_instance(self) -> None:
        result = inspect_skyrim_mo2_instance()
        self.instance_status.setText(result.get("message", "Could not inspect instance.") + ("\\n" + result.get("output", "") if result.get("output") else ""))
        self._append_log("Skyrim MO2 instance check: " + result.get("message", "unknown"))

    def create_skyrim_instance(self) -> None:
        preview = create_skyrim_mo2_instance(dry_run=True)
        if not preview.get("ok"):
            QMessageBox.warning(self, "Skyrim MO2 Instance", preview.get("message", "Preflight failed."))
            self._append_log("Skyrim instance preflight: " + preview.get("message", ""))
            return
        answer = QMessageBox.question(
            self, "Create Skyrim SE MO2 instance",
            "Ask STL to create its supported MO2 instance for Skyrim Special Edition (AppID 489830)?\\n\\n"
            "STL will use its own configured MO2 prefix and game metadata. An existing Skyrim instance is detected and left untouched. "
            "No Skyrim files, saves, Steam launch options, or existing mods are copied or overwritten by this app.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self._append_log("Skyrim instance creation cancelled.")
            return
        result = create_skyrim_mo2_instance(dry_run=False)
        self._append_log("Skyrim instance create: " + result.get("message", "unknown"))
        (QMessageBox.information if result.get("ok") else QMessageBox.warning)(self, "Skyrim MO2 Instance", result.get("message", "Operation failed.") + ("\\n\\n" + result.get("output", "") if result.get("output") else ""))
        self.refresh_skyrim_instance()

    def refresh_skyrim_mo2_config(self) -> None:
        state = inspect_skyrim_mo2_config()
        if state.get("exists"):
            self.skyrim_mo2_status.setText("Skyrim SE STL MO2 mode: " + str(state.get("mo2_mode") or "not explicitly set") + "\\n" + state["path"])
        else:
            self.skyrim_mo2_status.setText("No Skyrim-specific STL MO2 configuration exists. MO2 remains disabled for Skyrim by default.")

    def enable_skyrim_mo2(self) -> None:
        preview = configure_skyrim_mo2(dry_run=True, mode="gui")
        if not preview.get("ok"):
            QMessageBox.warning(self, "Skyrim MO2", preview.get("message", "Preflight failed."))
            return
        answer = QMessageBox.question(
            self, "Enable MO2 for Skyrim SE",
            "Create a new per-game STL config for AppID 489830 with MO2MODE=gui?\\n\\n"
            "This does not edit Steam launch options, game files, saves, mods, Proton prefixes, or existing MO2 instances.\\n"
            "If a per-game config already exists, it will be left untouched. The file can be disabled later from this page.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self._append_log("Skyrim MO2 config creation cancelled.")
            return
        result = configure_skyrim_mo2(dry_run=False, mode="gui")
        self._append_log("Skyrim MO2 config: " + result.get("message", "unknown result"))
        if result.get("ok"):
            QMessageBox.information(self, "Skyrim MO2", result["message"] + "\\n\\nRestart Steam before testing the game launch.")
        else:
            QMessageBox.warning(self, "Skyrim MO2", result.get("message", "Could not configure MO2."))
        self.refresh_skyrim_mo2_config()

    def disable_skyrim_mo2(self) -> None:
        answer = QMessageBox.question(
            self, "Disable Skyrim MO2 configuration",
            "Move only the STL-Steam-managed Skyrim config to a backup file?\\n\\nUnmanaged files are never removed, and the backup will not be overwritten.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        result = remove_managed_skyrim_mo2_config()
        self._append_log("Disable Skyrim MO2 config: " + result.get("message", "unknown result"))
        (QMessageBox.information if result.get("ok") else QMessageBox.warning)(self, "Skyrim MO2", result.get("message", "Operation failed."))
        self.refresh_skyrim_mo2_config()

    def run_mo2_action(self, command: str) -> None:
        preview = run_mo2_command(command, dry_run=True)
        if not preview.get("ok"):
            QMessageBox.warning(self, "MO2 Setup", preview.get("message", "Preflight failed."))
            self._append_log("MO2 " + command + " preflight failed: " + preview.get("message", ""))
            return
        prompt = ("Install Mod Organizer 2 using STL? This will install into STL's managed MO2 prefix. "
                  "Detected existing MO2 installs are not overwritten.") if command == "install" else (
                  "Launch MO2 standalone using STL? This opens MO2 in its own prefix. Create a new instance in MO2 if prompted; "
                  "the setup app will not copy or migrate existing mods, saves, or profiles.")
        answer = QMessageBox.question(self, "MO2 " + command.title(), prompt, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            self._append_log("MO2 " + command + " cancelled by user.")
            return
        result = run_mo2_command(command, dry_run=False)
        self._append_log("MO2 " + command + ": " + result.get("message", "unknown result"))
        if result.get("ok"):
            QMessageBox.information(self, "MO2 Setup", result.get("message", "Completed.") + ("\n\nMO2 is ready to configure an instance." if command == "start" else ""))
        else:
            details = result.get("output", "")
            QMessageBox.warning(self, "MO2 Setup", result.get("message", "Failed.") + ("\n\n" + details if details else ""))
        self.refresh_mo2()

    def compatibility(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        heading = QLabel("Compatibility")
        heading.setObjectName("heading")
        intro = QLabel("Install upstream SteamTinkerLaunch into a user-local prefix and register it as a Steam Compatibility Tool. Steam launch settings are not edited.")
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(intro)
        self.stl_result = card("SteamTinkerLaunch", "Checking user-local and compatibility-tools locations…")
        layout.addWidget(self.stl_result)
        refresh = QPushButton("Refresh STL detection")
        refresh.clicked.connect(self.refresh_stl)
        layout.addWidget(refresh)
        bootstrap = QPushButton("Install / Update STL-Steam")
        bootstrap.clicked.connect(self.install_stl_steam_bootstrap)
        layout.addWidget(bootstrap)
        self.bootstrap_status = QLabel("STL-Steam application installer status: idle")
        self.bootstrap_status.setObjectName("muted")
        self.bootstrap_status.setWordWrap(True)
        layout.addWidget(self.bootstrap_status)
        install = QPushButton("Install as Steam Compatibility Tool")
        install.clicked.connect(self.install_stl_compatibility)
        layout.addWidget(install)
        self.launch_note = QLabel("Steam launch configuration is not modified by this prototype.")
        self.launch_note.setObjectName("muted")
        self.launch_note.setWordWrap(True)
        layout.addWidget(self.launch_note)
        layout.addStretch(1)
        return page

    def install_stl_steam_bootstrap(self) -> None:
        script = Path(__file__).resolve().parent.parent / "install-skyrim-stl.sh"
        if not script.is_file():
            QMessageBox.warning(self, "Install STL-Steam", "The installer script was not found in the project folder:\\n" + str(script))
            self._append_log("STL-Steam bootstrap script missing: " + str(script))
            return
        answer = QMessageBox.question(
            self, "Install STL-Steam",
            "Run the bundled installer to detect Steam and Skyrim SE, then download STL-Steam into your user-local data directory.\\n\\n"
            "This does not change Steam launch options, Skyrim files, saves, mods, or existing MO2 instances.\\n\\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self._append_log("STL-Steam bootstrap cancelled.")
            return
        if getattr(self, "bootstrap_process", None) and self.bootstrap_process.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(self, "Install STL-Steam", "The installer is already running.")
            return
        self.bootstrap_process = QProcess(self)
        self.bootstrap_process.setProgram("bash")
        self.bootstrap_process.setArguments([str(script), "--install"])
        self.bootstrap_process.setWorkingDirectory(str(script.parent))
        self.bootstrap_process.readyReadStandardOutput.connect(self._read_bootstrap_output)
        self.bootstrap_process.readyReadStandardError.connect(self._read_bootstrap_output)
        self.bootstrap_process.finished.connect(self._bootstrap_finished)
        self.bootstrap_status.setText("Installing STL-Steam… See Logs for live output.")
        self._append_log("Starting bundled install-skyrim-stl.sh --install from the Qt UI.")
        self.bootstrap_process.start()
        if not self.bootstrap_process.waitForStarted(3000):
            self.bootstrap_status.setText("Installer could not start.")
            self._append_log("STL-Steam bootstrap failed to start: " + self.bootstrap_process.errorString())
            QMessageBox.warning(self, "Install STL-Steam", "Could not start the installer.\\n" + self.bootstrap_process.errorString())

    def _read_bootstrap_output(self) -> None:
        process = getattr(self, "bootstrap_process", None)
        if not process:
            return
        output = bytes(process.readAllStandardOutput()).decode(errors="replace")
        errors = bytes(process.readAllStandardError()).decode(errors="replace")
        if output.strip():
            self._append_log(output.rstrip())
        if errors.strip():
            self._append_log(errors.rstrip())

    def _bootstrap_finished(self, exit_code: int, exit_status) -> None:
        self._read_bootstrap_output()
        if exit_code == 0:
            self.bootstrap_status.setText("STL-Steam installer completed successfully.")
            QMessageBox.information(self, "Install STL-Steam", "Installer completed successfully. Review Logs for details.")
        else:
            self.bootstrap_status.setText(f"STL-Steam installer failed (exit code {exit_code}).")
            QMessageBox.warning(self, "Install STL-Steam", f"Installer failed with exit code {exit_code}.\\nOpen Logs for the exact error and next step.")
        self._append_log(f"STL-Steam bootstrap exited with code {exit_code}.")
        self.refresh_detection()
        self.refresh_stl()

    def refresh_stl(self) -> None:
        result = inspect_stl_installation()
        if result["installed"]:
            detail = "Executable(s):\n" + "\n".join(result["executables"])
            detail += "\n\nCompatibility-tool directory detected: " + ("Yes" if result["compatibility_tool_present"] else "No")
            status = "STL executable detected"
        else:
            detail = "No executable found in the user-local install, PATH, or common compatibility-tools directories."
            status = "STL not detected"
        self.stl_result = self._replace_card(self.compatibility_page, self.stl_result, card(status, detail))
        self._append_log("STL detection: " + status)
        compat = inspect_compatibility_tool()
        self._append_log("Steam compatibility tool: " + ("installed" if compat["installed"] else "not installed"))

    def install_stl_compatibility(self) -> None:
        preview = install_compatibility_tool(dry_run=True)
        if not preview.get("ok"):
            QMessageBox.warning(self, "STL compatibility tool", preview.get("message", "Preflight failed."))
            self._append_log("STL compatibility install preflight failed: " + preview.get("message", ""))
            return
        targets = "\n".join(preview.get("targets", []))
        answer = QMessageBox.question(
            self,
            "Install STL Compatibility Tool",
            "If STL is missing, it will be cloned into ~/stl/prefix. Then the upstream `compat add` command registers it with Steam.\n\n"
            "It will create a Steam compatibility-tool entry and will not change Skyrim, saves, mods, or MO2 instances.\n\n"
            "Target(s):\n" + targets + "\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self._append_log("STL compatibility installation cancelled by user.")
            return
        result = install_compatibility_tool(dry_run=False)
        self._append_log("STL compatibility install: " + result.get("message", "unknown result"))
        if result.get("ok"):
            QMessageBox.information(self, "STL Compatibility Tool", result.get("message", "Installed.") + "\n\nRestart Steam to make it discover the tool.")
        else:
            details = result.get("output", "")
            QMessageBox.warning(self, "STL Compatibility Tool", result.get("message", "Installation failed.") + ("\n\n" + details if details else ""))
        self.refresh_stl()

    def logs(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        heading = QLabel("Logs")
        heading.setObjectName("heading")
        intro = QLabel("Session diagnostics from read-only inspection. No external log files are collected yet.")
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(intro)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Run a detection refresh to populate diagnostics.")
        self.log_view.setMaximumBlockCount(500)
        layout.addWidget(self.log_view, 1)
        return page

    def refresh_detection(self) -> None:
        result = detect_skyrim()
        if result.get("found"):
            detail = "Detected at:\n" + result["game_dir"] + "\n\nSteam root: " + result["steam_root"]
            status = "Skyrim Special Edition detected"
        else:
            roots = result.get("steam_roots", [])
            detail = "Skyrim SE (AppID 489830) was not found.\n\nSteam roots checked:\n" + ("\n".join(roots) if roots else "No standard Steam installation found.")
            status = "Skyrim not detected"
        self.detect_result = self._replace_card(self.detection_page, self.detect_result, card(status, detail))
        self.game_summary = self._replace_card(self.overview_page, self.game_summary, card(status, detail))
        self._append_log("Game detection: " + status + (" — " + result["game_dir"] if result.get("found") else ""))

    def _append_log(self, message: str) -> None:
        if hasattr(self, "log_view"):
            self.log_view.appendPlainText(message)

    @staticmethod
    def _replace_card(page: QWidget, old: QFrame, new: QFrame) -> QFrame:
        layout = page.layout()
        index = layout.indexOf(old)
        if index >= 0:
            layout.removeWidget(old)
            old.deleteLater()
            layout.insertWidget(index, new)
        return new

    @staticmethod
    def placeholder(title: str, text: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(title)
        label.setObjectName("heading")
        description = QLabel(text)
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(label)
        layout.addWidget(description)
        layout.addStretch(1)
        return page

def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
