import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mo2_setup import inspect_mo2_installation, mo2_executable_candidates, run_mo2_command

class MO2SetupTests(unittest.TestCase):
    def fixture(self, home: Path):
        stl = home / ".local/share/stl-steam/bin/steamtinkerlaunch"
        stl.parent.mkdir(parents=True)
        stl.write_text("#!/bin/sh\n")
        stl.chmod(0o755)
        return stl

    def test_install_dry_run_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.fixture(home)
            result = run_mo2_command("install", home, dry_run=True)
            self.assertTrue(result["ok"])
            self.assertTrue(result["dry_run"])
            self.assertFalse((home / ".config").exists())

    def test_existing_mo2_install_is_preserved_and_install_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.fixture(home)
            existing = home / ".config/steamtinkerlaunch/mo2/compatdata/pfx/drive_c/Modding/MO2/ModOrganizer.exe"
            existing.parent.mkdir(parents=True)
            existing.write_bytes(b"preserve")
            result = run_mo2_command("install", home, dry_run=False)
            self.assertFalse(result["ok"])
            self.assertEqual(existing.read_bytes(), b"preserve")

    def test_start_refused_without_existing_mo2(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.fixture(home)
            result = run_mo2_command("start", home, dry_run=False)
            self.assertFalse(result["ok"])

    def test_install_command_verifies_executable_after_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.fixture(home)
            target = home / ".config/steamtinkerlaunch/mo2/compatdata/pfx/drive_c/Modding/MO2/ModOrganizer.exe"
            def fake_run(command, **kwargs):
                target.parent.mkdir(parents=True)
                target.write_bytes(b"fixture")
                return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(home / ".config")}):
                with patch("mo2_setup.subprocess.run", side_effect=fake_run):
                    result = run_mo2_command("install", home, dry_run=False)
            self.assertTrue(result["ok"], result)
            self.assertTrue(target.exists())

if __name__ == "__main__":
    unittest.main()
