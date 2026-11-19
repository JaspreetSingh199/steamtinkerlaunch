#!/usr/bin/env python3
"""Qt 6 desktop application for Wyrd's Skyrim + Mod Organizer 2 workflow."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout,
    QWidget,
)

from skyrim_detection import detect_skyrim
from wyrd_mo2 import (
    discover_proton_builds, inspect_wyrd_installation,
    install_mo2_environment, launch_mo2, managed_paths,
)

STYLE = """
QWidget { background: #15171b; color: #e5e7eb; font-size: 14px; }
QFrame#panel { background: #20232a; border: 1px solid #343943; border-radius: 12px; }
QLabel#heading { font-size: 27px; font-weight: 650; }
QLabel#section { font-size: 17px; font-weight: 600; }
QLabel#muted { color: #a2aab6; }
QPushButton { background: #354255; border: 1px solid #526176; border-radius: 8px; padding: 11px 17px; }
QPushButton:hover { background: #40516a; }
QPushButton:disabled { color: #818995; background: #262a31; }
QComboBox { background: #252a33; border: 1px solid #414a58; border-radius: 7px; padding: 9px; }
QProgressBar { background: #252a33; border: 0; border-radius: 5px; height: 12px; text-align: center; }
QProgressBar::chunk { background: #5b8def; border-radius: 5px; }
QPlainTextEdit { background: #111318; border: 1px solid #303641; border-radius: 8px; }
"""


def panel(title: str, description: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(17, 15, 17, 15)
    heading = QLabel(title)
    heading.setObjectName("section")
    detail = QLabel(description)
    detail.setObjectName("muted")
    detail.setWordWrap(True)
    layout.addWidget(heading)
    layout.addWidget(detail)
    frame.detail_label = detail
    return frame


class InstallWorker(QThread):
    progress = Signal(int, str)
    completed = Signal(dict)

    def __init__(self, proton_path: str, game_path: str):
        super().__init__()
        self.proton_path = Path(proton_path)
        self.game_path = Path(game_path)

    def run(self) -> None:
        try:
            result = install_mo2_environment(
                self.proton_path, self.game_path,
                callback=lambda value, message: self.progress.emit(value, message),
            )
        except Exception as error:
            result = {"ok": False, "message": str(error)}
        self.completed.emit(result)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Wyrd — Skyrim Modding Environment")
        self.resize(980, 700)
        self.worker: InstallWorker | None = None
        self.game_state: dict = {"found": False}
        self.proton_builds: list[dict] = []
        self.mo2_state: dict = {"installed": False}

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(25, 22, 25, 22)
        layout.setSpacing(14)

        heading = QLabel("Wyrd")
        heading.setObjectName("heading")
        subtitle = QLabel("A focused Skyrim Special Edition + Mod Organizer 2 setup for Linux")
        subtitle.setObjectName("muted")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        self.game_panel = panel("1. Skyrim Special Edition", "Detecting Steam libraries…")
        layout.addWidget(self.game_panel)

        runtime_panel = QFrame()
        runtime_panel.setObjectName("panel")
        runtime_layout = QVBoxLayout(runtime_panel)
        runtime_layout.setContentsMargins(17, 15, 17, 15)
        runtime_heading = QLabel("2. Proton runtime")
        runtime_heading.setObjectName("section")
        runtime_detail = QLabel("Wyrd uses a compatible Proton build to run MO2 in its own isolated prefix.")
        runtime_detail.setObjectName("muted")
        runtime_detail.setWordWrap(True)
        runtime_layout.addWidget(runtime_heading)
        runtime_layout.addWidget(runtime_detail)
        runtime_row = QHBoxLayout()
        self.proton_combo = QComboBox()
        self.proton_combo.setMinimumWidth(420)
        self.refresh_button = QPushButton("Refresh detection")
        self.refresh_button.clicked.connect(self.refresh_all)
        runtime_row.addWidget(self.proton_combo, 1)
        runtime_row.addWidget(self.refresh_button)
        runtime_layout.addLayout(runtime_row)
        self.runtime_status = QLabel("Looking for Proton…")
        self.runtime_status.setObjectName("muted")
        runtime_layout.addWidget(self.runtime_status)
        layout.addWidget(runtime_panel)

        self.mo2_panel = panel("3. Mod Organizer 2", "Checking Wyrd's managed installation…")
        layout.addWidget(self.mo2_panel)

        action_row = QHBoxLayout()
        self.install_button = QPushButton("Install MO2")
        self.install_button.clicked.connect(self.install_mo2)
        self.launch_button = QPushButton("Launch MO2")
        self.launch_button.clicked.connect(self.start_mo2)
        self.launch_button.setEnabled(False)
        action_row.addWidget(self.install_button)
        action_row.addWidget(self.launch_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self.progress_label = QLabel("Ready")
        self.progress_label.setObjectName("muted")
        layout.addWidget(self.progress_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        instructions = panel(
            "4. Launch Skyrim from MO2",
            "On the first MO2 launch, create a new instance and choose “Skyrim Special Edition”. "
            "Wyrd registers your detected game path only inside its own Proton prefix. "
            "After the instance is created, select Skyrim or SKSE in MO2's executable dropdown and press Run. "
            "MO2 then launches the game through its mod virtual filesystem.",
        )
        layout.addWidget(instructions)

        logs_heading = QLabel("Setup log")
        logs_heading.setObjectName("section")
        layout.addWidget(logs_heading)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(400)
        self.log_view.setPlaceholderText("Detection and installation progress will appear here.")
        layout.addWidget(self.log_view, 1)

        self.setCentralWidget(root)
        self.refresh_all()

    def _log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def refresh_all(self) -> None:
        selected = self.proton_combo.currentData()
        self.game_state = detect_skyrim()
        if self.game_state.get("found"):
            game_path = self.game_state["game_dir"]
            self.game_panel.detail_label.setText(
                "Detected:\n" + game_path +
                "\nSteam library: " + self.game_state.get("library", "detected")
            )
            self._log("Skyrim SE detected: " + game_path)
        else:
            roots = self.game_state.get("steam_roots", [])
            self.game_panel.detail_label.setText(
                "Skyrim Special Edition (AppID 489830) was not found. "
                "Install it through Steam and refresh detection.\nSteam roots checked: " +
                (", ".join(roots) if roots else "No Steam library detected.")
            )
            self._log("Skyrim SE not detected.")

        self.proton_builds = discover_proton_builds()
        self.proton_combo.clear()
        selected_index = -1
        for build in self.proton_builds:
            label = f'{build["name"]} ({build["architecture"]})'
            self.proton_combo.addItem(label, build["path"])
            self.proton_combo.setItemData(self.proton_combo.count() - 1, build["path"], 3)
            if selected and selected == build["path"]:
                selected_index = self.proton_combo.count() - 1
        if selected_index >= 0:
            self.proton_combo.setCurrentIndex(selected_index)
        if self.proton_builds:
            self.runtime_status.setText(
                f'{len(self.proton_builds)} compatible Proton build(s) found. '
                "The selected runtime will be saved with this Wyrd installation."
            )
            self._log("Proton discovery: " + ", ".join(item["name"] for item in self.proton_builds))
        else:
            self.runtime_status.setText(
                "No compatible Proton build found. Install a current x86_64 Proton build through Steam or ProtonUp-Qt, then refresh."
            )
            self._log("No compatible Proton builds found.")

        self.mo2_state = inspect_wyrd_installation()
        if self.mo2_state.get("installed"):
            version = self.mo2_state.get("metadata", {}).get("version", "unknown version")
            prefix = "ready" if self.mo2_state.get("prefix_ready") else "incomplete"
            self.mo2_panel.detail_label.setText(
                f"MO2 {version} is installed and verified.\n"
                f'Executable: {self.mo2_state.get("executable")}\n'
                f'Wyrd Proton prefix: {prefix}'
            )
            self.launch_button.setEnabled(bool(self.mo2_state.get("prefix_ready")))
            self.install_button.setText("Recheck MO2" if self.mo2_state.get("prefix_ready") else "Repair MO2 runtime")
            self._log("Wyrd MO2 inspection: verified " + version)
        else:
            external = self.mo2_state.get("external_installations", [])
            description = self.mo2_state.get("message", "MO2 is not installed.")
            if external:
                description += "\nExisting installation(s):\n" + "\n".join(external)
                description += "\nThese copies are left untouched; Wyrd installs into its own managed location."
            self.mo2_panel.detail_label.setText(description)
            self.launch_button.setEnabled(False)
            self.install_button.setText("Install MO2")
            self._log("Wyrd MO2 inspection: " + description)

        ready = bool(self.game_state.get("found") and self.proton_builds)
        self.install_button.setEnabled(ready and not (self.worker and self.worker.isRunning()))
        self.proton_combo.setEnabled(bool(self.proton_builds) and not (self.worker and self.worker.isRunning()))

    def install_mo2(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        if not self.game_state.get("found"):
            QMessageBox.warning(self, "Wyrd setup", "Skyrim Special Edition was not detected. Install it through Steam, then refresh.")
            return
        proton_path = self.proton_combo.currentData()
        if not proton_path:
            QMessageBox.warning(self, "Wyrd setup", "No compatible Proton build is selected.")
            return
        if self.mo2_state.get("installed") and self.mo2_state.get("prefix_ready"):
            self.start_mo2()
            return
        answer = QMessageBox.question(
            self, "Install Mod Organizer 2",
            "Wyrd will download the official MO2 release, install it into a Wyrd-managed folder, "
            "and initialize a separate Proton prefix for MO2.\n\n"
            "Your Skyrim files, Steam prefix, saves, and any existing MO2 installation will not be modified.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        game_path = self.game_state["game_dir"]
        self.worker = InstallWorker(str(proton_path), str(game_path))
        self.worker.progress.connect(self._on_install_progress)
        self.worker.completed.connect(self._on_install_completed)
        self.install_button.setEnabled(False)
        self.launch_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.proton_combo.setEnabled(False)
        self.progress.setValue(0)
        self.progress_label.setText("Starting MO2 setup…")
        self._log("Starting Wyrd-owned MO2 installation.")
        self.worker.start()

    def _on_install_progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.progress_label.setText(message)
        self._log(message)

    def _on_install_completed(self, result: dict) -> None:
        if result.get("ok"):
            self.progress.setValue(100)
            self.progress_label.setText("MO2 installed and verified.")
            self._log(result.get("message", "MO2 setup completed."))
            QMessageBox.information(
                self, "Wyrd setup complete",
                result.get("message", "MO2 is ready.") +
                "\n\nPress Launch MO2. On first launch, create a Skyrim Special Edition instance in MO2."
            )
        else:
            self.progress_label.setText("Setup stopped. Review the log for details.")
            self._log("MO2 setup failed: " + result.get("message", "Unknown error"))
            QMessageBox.warning(self, "Wyrd setup failed", result.get("message", "MO2 setup failed."))
        self.refresh_button.setEnabled(True)
        self.refresh_all()

    def _has_instance(self) -> bool:
        prefix = managed_paths()["prefix"] / "pfx/drive_c/users/steamuser/AppData/Local/ModOrganizer/instances"
        try:
            return any((entry / "ModOrganizer.ini").is_file() for entry in prefix.iterdir() if entry.is_dir())
        except OSError:
            return False

    def start_mo2(self) -> None:
        first_run = not self._has_instance()
        result = launch_mo2(pick_instance=first_run)
        self._log(result.get("message", "MO2 launch failed."))
        if result.get("ok"):
            self.progress_label.setText("MO2 launched through Proton.")
            if first_run:
                QMessageBox.information(
                    self, "First MO2 launch",
                    "MO2 has been opened in its instance picker.\n\n"
                    "Create a new instance and select Skyrim Special Edition. "
                    "Then choose Skyrim or SKSE in MO2's executable dropdown and press Run."
                )
        else:
            QMessageBox.warning(self, "Launch MO2", result.get("message", "Could not launch MO2."))

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            QMessageBox.information(
                self, "Setup is running",
                "MO2 installation is still running. Wait for it to finish before closing Wyrd."
            )
            event.ignore()
            return
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
