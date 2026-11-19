import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mo2_setup import (
    create_skyrim_mo2_instance,
    inspect_skyrim_mo2_instance,
    run_mo2_command,
    proton_binary_architecture,
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

    def test_proton_architecture_rejects_aarch64_on_x86_64_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wine = root / "files/bin/wine"
            wine.parent.mkdir(parents=True)
            header = bytearray(20)
            header[:4] = bytes([0x7f, 69, 76, 70])
            header[4] = 2
            header[5] = 1
            header[18:20] = (183).to_bytes(2, "little")
            wine.write_bytes(header)
            uname = type("Uname", (), {"machine": "x86_64"})()
            with patch("mo2_setup.os.uname", return_value=uname):
                result = proton_binary_architecture(root)
            self.assertFalse(result["ok"])
            self.assertEqual(result["architecture"], "AArch64")
            self.assertIn("Choose a Proton build", result["message"])

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
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(home / ".config")}):
                result = run_mo2_command("install", home, dry_run=False)
            self.assertFalse(result["ok"])
            self.assertEqual(exe.read_bytes(), b"preserve")

    def test_mo2_install_starts_visible_process_without_capturing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            stl = home / ".local/share/stl-steam/bin/steamtinkerlaunch"
            stl.parent.mkdir(parents=True)
            stl.write_text("#!/bin/sh\\n")
            stl.chmod(0o755)
            with patch("mo2_setup.subprocess.Popen") as popen:
                popen.return_value.pid = 4321
                result = run_mo2_command("install", home, dry_run=False)
            self.assertTrue(result["ok"])
            self.assertEqual(result["pid"], 4321)
            kwargs = popen.call_args.kwargs
            self.assertIsNone(kwargs["stdout"])
            self.assertIsNone(kwargs["stderr"])
            self.assertIsNone(kwargs["stdin"])
            self.assertTrue(kwargs["start_new_session"])

    def test_mo2_install_reports_start_only_and_does_not_capture_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            stl = home / ".local/share/stl-steam/bin/steamtinkerlaunch"
            stl.parent.mkdir(parents=True)
            stl.write_text("#!/bin/sh\\n")
            stl.chmod(0o755)
            with patch("mo2_setup.subprocess.Popen") as popen:
                popen.return_value.pid = 4321
                result = run_mo2_command("install", home, dry_run=False)
            self.assertTrue(result["ok"])
            self.assertIn("start only", result["message"])
            self.assertEqual(result["pid"], 4321)
            self.assertIsNone(popen.call_args.kwargs["stdout"])
            self.assertIsNone(popen.call_args.kwargs["stderr"])
            self.assertIsNone(popen.call_args.kwargs["stdin"])
            self.assertTrue(popen.call_args.kwargs["start_new_session"])

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
            created = {"value": False}
            def fake_run(args, **kwargs):
                calls.append(args)
                if args[-3:] == ["mo2", "create-instance", "489830"]:
                    created["value"] = True
                    return type("Result", (), {"returncode": 0, "stdout": "created", "stderr": ""})()
                listing = "Skyrim Special Edition (489830) -> /prefix" if created["value"] else "No installed MO2 instances"
                return type("Result", (), {"returncode": 0, "stdout": listing, "stderr": ""})()
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(home / ".config")}):
                with patch("mo2_setup.subprocess.run", side_effect=fake_run):
                    result = create_skyrim_mo2_instance(home, dry_run=False)
            self.assertTrue(result["ok"], result)
            self.assertTrue(any(call[-3:] == ["mo2", "create-instance", "489830"] for call in calls))


if __name__ == "__main__":
    unittest.main()
