import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo2_inspection import (
    find_mo2_installations,
    inspect_mo2,
    inspect_stl_installation,
    inspect_skyrim_compatibility,
)


class MO2InspectionTests(unittest.TestCase):
    def test_detects_known_mo2_without_modifying_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            mo2 = home / "Games/ModOrganizer"
            mo2.mkdir(parents=True)
            exe = mo2 / "ModOrganizer.exe"
            exe.write_bytes(b"fixture")
            before = exe.read_bytes()
            self.assertEqual(find_mo2_installations(home), [mo2.resolve()])
            self.assertTrue(inspect_mo2(home)["found"])
            self.assertEqual(exe.read_bytes(), before)
            self.assertEqual(list(home.iterdir()), [home / "Games"])

    def test_mo2_missing_is_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.assertFalse(inspect_mo2(home)["found"])
            self.assertEqual(list(home.iterdir()), [])

    def test_inspects_stl_without_installing(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            data = home / "data"
            with patch.dict(os.environ, {"XDG_DATA_HOME": str(data)}):
                result = inspect_stl_installation(home)
            self.assertFalse(result["installed"])
            self.assertFalse(data.exists())

    def test_detects_stl_installed_by_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            executable = home / "stl/prefix/steamtinkerlaunch"
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\\n")
            executable.chmod(0o755)
            result = inspect_stl_installation(home)
            self.assertTrue(result["installed"])
            self.assertIn(str(executable.resolve()), result["executables"])
            self.assertFalse(result["compatibility_tool_present"])

    def test_reports_existing_stl_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            executable = home / ".steam/steam/compatibilitytools.d/SteamTinkerLaunch/steamtinkerlaunch"
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\n")
            executable.chmod(0o755)
            result = inspect_stl_installation(home)
            self.assertTrue(result["installed"])
            self.assertTrue(result["compatibility_tool_present"])

    def test_compat_registration_detected_when_executable_symlink_resolves_outside(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            source = home / "stl/prefix/steamtinkerlaunch"
            source.parent.mkdir(parents=True)
            source.write_text("#!/bin/sh\\n")
            source.chmod(0o755)
            compat = home / ".steam/steam/compatibilitytools.d/SteamTinkerLaunch"
            compat.mkdir(parents=True)
            (compat / "steamtinkerlaunch").symlink_to(source)
            result = inspect_stl_installation(home)
            self.assertTrue(result["installed"])
            self.assertTrue(result["compatibility_tool_present"])

    def test_reads_existing_steam_config_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            steam = Path(tmp) / ".local/share/Steam"
            config = steam / "userdata/123/config/localconfig.vdf"
            config.parent.mkdir(parents=True)
            config.write_text('"489830" { "CompatTool" "steamtinkerlaunch" }')
            before = config.read_bytes()
            result = inspect_skyrim_compatibility(steam)
            self.assertTrue(result["stl_reference_found"])
            self.assertEqual(config.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
