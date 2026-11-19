import os
import tempfile
from unittest.mock import patch
import unittest
from pathlib import Path
from stl_compatibility import (
    configure_skyrim_mo2, inspect_skyrim_mo2_config,
    remove_managed_skyrim_mo2_config, skyrim_game_config_path,
)

class SkyrimMO2ConfigTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"XDG_CONFIG_HOME": str(Path(self._testMethodName + '-config').resolve())})
        self.env.start()

    def tearDown(self):
        self.env.stop()
    def test_config_path_matches_stl_runtime_resolver(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            expected = Path(os.environ["XDG_CONFIG_HOME"]) / "steamtinkerlaunch/gamecfgs/id/489830.conf"
            self.assertEqual(skyrim_game_config_path(home), expected)

    def test_dry_run_does_not_create_config_or_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = configure_skyrim_mo2(home, dry_run=True)
            self.assertTrue(result["ok"])
            self.assertFalse(skyrim_game_config_path(home).exists())
            self.assertFalse((home / ".config").exists())

    def test_creates_only_missing_skyrim_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = configure_skyrim_mo2(home, dry_run=False, mode="gui")
            self.assertTrue(result["ok"])
            state = inspect_skyrim_mo2_config(home)
            self.assertTrue(state["exists"])
            self.assertEqual(state["mo2_mode"], "gui")
            self.assertTrue(Path(state["path"]).read_text().startswith("# Managed by STL-Steam."))

    def test_existing_user_config_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            path = skyrim_game_config_path(home)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('MO2MODE="disabled"\nCUSTOM="keep"\n')
            before = path.read_bytes()
            result = configure_skyrim_mo2(home, dry_run=False)
            self.assertFalse(result["ok"])
            self.assertEqual(path.read_bytes(), before)

    def test_managed_config_can_be_reversibly_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            created = configure_skyrim_mo2(home, dry_run=False)
            path = Path(created["path"])
            original = path.read_bytes()
            result = remove_managed_skyrim_mo2_config(home)
            self.assertTrue(result["ok"])
            backup = Path(result["backup"])
            self.assertEqual(backup.read_bytes(), original)
            self.assertFalse(path.exists())

    def test_unmanaged_config_cannot_be_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            path = skyrim_game_config_path(home)
            path.parent.mkdir(parents=True)
            path.write_text('MO2MODE="gui"\n')
            result = remove_managed_skyrim_mo2_config(home)
            self.assertFalse(result["ok"])
            self.assertTrue(path.exists())

if __name__ == "__main__":
    unittest.main()
