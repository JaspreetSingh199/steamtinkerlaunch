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


@unittest.skipIf(QApplication is None, "PySide6 is an optional desktop dependency")
class MainWindowSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _window(self, state=None, game=None, builds=None):
        game = game or {
            "found": True, "game_dir": "/games/Skyrim Special Edition",
            "steam_root": "/home/test/.steam/steam", "library": "/home/test/.steam/steam/steamapps",
        }
        builds = builds if builds is not None else [{
            "name": "Proton Test", "path": "/home/test/.steam/steam/steamapps/common/Proton Test",
            "architecture": "x86_64",
        }]
        state = state or {
            "installed": False, "prefix_ready": False, "external_installations": [],
            "message": "MO2 is not installed yet.",
        }
        patches = [
            patch("main.detect_skyrim", return_value=game),
            patch("main.discover_proton_builds", return_value=builds),
            patch("main.inspect_wyrd_installation", return_value=state),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        return MainWindow()

    def test_window_is_branded_wyrd_and_has_only_the_core_setup_flow(self):
        window = self._window()
        self.assertEqual(window.windowTitle(), "Wyrd — Skyrim Modding Environment")
        self.assertTrue(window.game_state["found"])
        self.assertEqual(window.proton_combo.count(), 1)
        self.assertEqual(window.install_button.text(), "Install MO2")
        self.assertFalse(window.launch_button.isEnabled())
        self.assertFalse(hasattr(window, "nav"))
        window.close()

    def test_install_is_enabled_only_when_game_and_proton_are_detected(self):
        window = self._window(builds=[])
        self.assertFalse(window.install_button.isEnabled())
        self.assertIn("No compatible Proton", window.runtime_status.text())
        window.close()

    def test_external_mo2_is_reported_but_not_adopted(self):
        state = {
            "installed": False, "prefix_ready": False,
            "external_installations": ["/home/test/Games/ModOrganizer"],
            "message": "An MO2 installation exists elsewhere. Wyrd will not overwrite or adopt it.",
        }
        window = self._window(state=state)
        self.assertIn("left untouched", window.mo2_panel.detail_label.text())
        self.assertTrue(window.install_button.isEnabled())
        window.close()

    def test_incomplete_wyrd_prefix_offers_repair_not_launch(self):
        state = {
            "installed": True, "prefix_ready": False,
            "executable": "/home/test/.local/share/wyrd/mo2/ModOrganizer.exe",
            "metadata": {"version": "v2.5.2"},
            "external_installations": [],
        }
        window = self._window(state=state)
        self.assertEqual(window.install_button.text(), "Repair MO2 runtime")
        self.assertTrue(window.install_button.isEnabled())
        self.assertFalse(window.launch_button.isEnabled())
        window.close()


if __name__ == "__main__":
    unittest.main()
