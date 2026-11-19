import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from PySide6.QtWidgets import QApplication
    from main import MainWindow
except ImportError:
    QApplication = None
    MainWindow = None


class MainWindowSmokeTests(unittest.TestCase):
    @unittest.skipIf(QApplication is None, "PySide6 is an optional desktop dependency")
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_all_navigation_pages_construct_and_switch(self):
        window = MainWindow()
        self.assertEqual(window.nav.count(), 5)
        self.assertEqual(window.pages.count(), 5)
        for index in range(5):
            window.nav.setCurrentRow(index)
            self.assertEqual(window.pages.currentIndex(), index)
        window.close()

    def test_refresh_handlers_are_read_only_and_log_results(self):
        window = MainWindow()
        with patch("main.detect_skyrim", return_value={"found": False, "steam_roots": []}):
            window.refresh_detection()
        with patch("main.inspect_mo2", return_value={"found": False, "installations": []}):
            window.refresh_mo2()
        with patch("main.inspect_stl_installation", return_value={"installed": False, "executables": [], "compatibility_tool_present": False}):
            window.refresh_stl()
        log = window.log_view.toPlainText()
        self.assertIn("Game detection:", log)
        self.assertIn("MO2 detection:", log)
        self.assertIn("STL detection:", log)
        window.close()


if __name__ == "__main__":
    unittest.main()
