#!/usr/bin/env python3
"""Qt 6 desktop shell for STL-Steam's Skyrim setup."""
from __future__ import annotations

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFrame, QLabel, QListWidget, QMainWindow, QPushButton,
    QStackedWidget, QVBoxLayout, QHBoxLayout, QWidget,
)
from skyrim_detection import detect_skyrim

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
        self.pages.addWidget(self.placeholder("MO2 Setup", "MO2 installation and instance setup will be enabled after the safe, per-game configuration path is verified."))
        self.pages.addWidget(self.placeholder("Compatibility", "Compatibility settings will be read first. Existing settings will never be silently overwritten."))
        self.pages.addWidget(self.placeholder("Logs", "Installer and STL-Steam logs will be displayed here."))
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        row.addWidget(self.nav)
        row.addWidget(self.pages, 1)
        self.setCentralWidget(root)
        self.refresh_detection()

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

    def refresh_detection(self) -> None:
        result = detect_skyrim()
        if result.get("found"):
            detail = "Detected at:\\n" + result["game_dir"] + "\\n\\nSteam root: " + result["steam_root"]
            status = "Skyrim Special Edition detected"
        else:
            roots = result.get("steam_roots", [])
            detail = "Skyrim SE (AppID 489830) was not found.\\n\\nSteam roots checked:\\n" + ("\\n".join(roots) if roots else "No standard Steam installation found.")
            status = "Skyrim not detected"
        self.detect_result = self._replace_card(self.detection_page, self.detect_result, card(status, detail))
        self.game_summary = self._replace_card(self.overview_page, self.game_summary, card(status, detail))

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
