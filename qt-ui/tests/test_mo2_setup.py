import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mo2_setup import (
    create_skyrim_mo2_instance,
    inspect_skyrim_mo2_instance,
    run_mo2_command,
)


class MO2SetupTests(unittest.TestCase):
    def setup_files(self, home: Path):
        stl = home / ".local/share/stl-steam/bin/steamtinkerlaunch"
        stl.parent.mkdir(parents=True)
        stl.write_text("#!/bin/sh\n")
        stl.chmod(0o755)
        exe = home / ".config/steamtinkerlaunch/compatdata/pfx/drive_c/Modding/MO2/ModOrganizer.exe"
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b"fixture")
        return stl, exe

    def test_install_refuses_to_overwrite_detected_mo2(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            stl = home / ".local/share/stl-steam/bin/steamtinkerlaunch"
            stl.parent.mkdir(parents=True)
            stl.write_text("#!/bin/sh\n")
            stl.chmod(0o755)
            exe = home / ".config/steamtinkerlaunch/compatdata/pfx/drive_c/Modding/MO2/ModOrganizer.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"preserve")
            result = run_mo2_command("install", home, dry_run=False)
            self.assertFalse(result["ok"])
            self.assertEqual(exe.read_bytes(), b"preserve")

    def test_create_instance_dry_run_does_not_change_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.setup_files(home)
            before = sorted(str(p.relative_to(home)) for p in home.rglob("*"))
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(home / ".config")}):
                result = create_skyrim_mo2_instance(home, dry_run=True)
            after = sorted(str(p.relative_to(home)) for p in home.rglob("*"))
            self.assertTrue(result["ok"])
            self.assertEqual(before, after)
            self.assertIn("489830", result["message"])

    def test_create_instance_refuses_when_mo2_not_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            stl = home / ".local/share/stl-steam/bin/steamtinkerlaunch"
            stl.parent.mkdir(parents=True)
            stl.write_text("#!/bin/sh\n")
            stl.chmod(0o755)
            result = create_skyrim_mo2_instance(home, dry_run=False)
            self.assertFalse(result["ok"])

    def test_create_instance_refuses_existing_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.setup_files(home)
            with patch("mo2_setup.inspect_skyrim_mo2_instance",
                       return_value={"ok": True, "installed": True, "output": "Skyrim Special Edition (489830)"}):
                with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(home / ".config")}):
                    result = create_skyrim_mo2_instance(home, dry_run=False)
            self.assertFalse(result["ok"])
            self.assertIn("not modified", result["message"])

    def test_create_instance_calls_supported_stl_command_and_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.setup_files(home)
            calls = []
            def fake_run(args, **kwargs):
                calls.append(args)
                if args[-3:] == ["mo2", "create-instance", "489830"]:
                    return type("Result", (), {"returncode": 0, "stdout": "created", "stderr": ""})()
                return type("Result", (), {"returncode": 0, "stdout": "Skyrim Special Edition (489830) -> /prefix", "stderr": ""})()
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(home / ".config")}):
                with patch("mo2_setup.subprocess.run", side_effect=fake_run):
                    result = create_skyrim_mo2_instance(home, dry_run=False)
            self.assertTrue(result["ok"], result)
            self.assertTrue(any(call[-3:] == ["mo2", "create-instance", "489830"] for call in calls))


if __name__ == "__main__":
    unittest.main()
