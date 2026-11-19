#!/usr/bin/env python3
"""Experimental Qt 6 UI shell for STL-Steam. Backend is intentionally not connected."""
from __future__ import annotations

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFrame, QLabel, QListWidget, QMainWindow, QProgressBar,
    QPushButton, QStackedWidget, QVBoxLayout, QHBoxLayout, QWidget,
)

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
QProgressBar { border: 0; background: #30343c; border-radius: 5px; height: 10px; }
QProgressBar::chunk { background: #60a5fa; border-radius: 5px; }
"""

def card(title: str, description: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
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

        nav = QListWidget()
        nav.setFixedWidth(210)
        nav.addItems(["Overview", "Game Detection", "MO2 Setup", "Compatibility", "Logs"])
        nav.setCurrentRow(0)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.overview())
        self.pages.addWidget(self.placeholder("Game Detection", "Detection will be connected to the reviewed installer logic."))
        self.pages.addWidget(self.placeholder("MO2 Setup", "A guided MO2 setup flow will be added after the runtime path is verified."))
        self.pages.addWidget(self.placeholder("Compatibility", "Proton and prefix controls will be added without changing existing settings silently."))
        self.pages.addWidget(self.placeholder("Logs", "Installer and STL-Steam logs will be displayed here."))
        nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        row.addWidget(nav)
        row.addWidget(self.pages, 1)
        self.setCentralWidget(root)

    def overview(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        heading = QLabel("Skyrim Setup")
        heading.setObjectName("heading")
        subtitle = QLabel("STL-Steam desktop frontend prototype")
        subtitle.setObjectName("muted")
        layout.addWidget(heading)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(card("Installer", "The bootstrap is still a separate, tested component. UI actions are not connected yet."))
        layout.addWidget(card("Game", "Skyrim Special Edition detection will be wired in after frontend/backend contracts are defined."))
        layout.addWidget(card("Mod Organizer 2", "MO2 installation and instance setup will use STL's own runtime logic."))
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setTextVisible(False)
        layout.addWidget(progress)
        buttons = QHBoxLayout()
        install = QPushButton("Install STL-Steam")
        install.setEnabled(False)
        setup = QPushButton("Configure MO2")
        setup.setEnabled(False)
        buttons.addWidget(install)
        buttons.addWidget(setup)
        layout.addLayout(buttons)
        layout.addStretch(1)
        layout.addWidget(QLabel("Prototype only — backend actions are disabled to avoid changing your system."))
        return page

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
