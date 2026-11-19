#!/usr/bin/env python3
"""Qt 6 desktop shell for STL-Steam's Skyrim setup."""
from __future__ import annotations

import sys
from PySide6.QtWidgets import (
    QApplication, QFrame, QLabel, QListWidget, QMainWindow, QPushButton,
    QStackedWidget, QVBoxLayout, QHBoxLayout, QWidget, QPlainTextEdit, QMessageBox,
)
from skyrim_detection import detect_skyrim
from mo2_inspection import inspect_mo2, inspect_stl_installation
from stl_compatibility import install_compatibility_tool, inspect_compatibility_tool

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
        note = QLabel("Read-only detection is enabled. Install and launch actions are not yet connected.")
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
        self._append_log("MO2 detection: " + status)

    def compatibility(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        heading = QLabel("Compatibility")
        heading.setObjectName("heading")
        intro = QLabel("STL is intended to be selected as the Steam Compatibility Tool for Proton games. This page only checks for a user-local STL executable; it does not change Steam settings.")
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(intro)
        self.stl_result = card("SteamTinkerLaunch", "Checking user-local and compatibility-tools locations…")
        layout.addWidget(self.stl_result)
        refresh = QPushButton("Refresh STL detection")
        refresh.clicked.connect(self.refresh_stl)
        layout.addWidget(refresh)
        install = QPushButton("Install as Steam Compatibility Tool")
        install.clicked.connect(self.install_stl_compatibility)
        layout.addWidget(install)
        self.launch_note = QLabel("Steam launch configuration is not modified by this prototype.")
        self.launch_note.setObjectName("muted")
        self.launch_note.setWordWrap(True)
        layout.addWidget(self.launch_note)
        layout.addStretch(1)
        return page

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
            "This will run SteamTinkerLaunch's supported `compat add` command.\n\n"
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
