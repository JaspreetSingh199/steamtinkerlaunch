import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from stl_compatibility import compatibility_tool_targets, find_stl_executable, install_compatibility_tool, inspect_compatibility_tool

class CompatibilityToolTests(unittest.TestCase):
    def fixture_home(self, root: Path):
        steam = root / ".local/share/Steam"
        (steam / "steamapps").mkdir(parents=True)
        exe = root / ".local/share/stl-steam/bin/steamtinkerlaunch"
        exe.parent.mkdir(parents=True)
        exe.write_text("#!/bin/sh\n")
        exe.chmod(0o755)
        return steam, exe

    def test_detects_user_local_stl_and_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, exe = self.fixture_home(home)
            self.assertEqual(find_stl_executable(home), exe.resolve())
            self.assertEqual(compatibility_tool_targets(home), [steam / "compatibilitytools.d/SteamTinkerLaunch"])
            self.assertFalse(inspect_compatibility_tool(home)["installed"])

    def test_dry_run_does_not_create_compatibility_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, exe = self.fixture_home(home)
            result = install_compatibility_tool(home, dry_run=True)
            self.assertTrue(result["ok"])
            self.assertTrue(result["dry_run"])
            self.assertFalse((steam / "compatibilitytools.d").exists())

    def test_existing_target_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, exe = self.fixture_home(home)
            target = steam / "compatibilitytools.d/SteamTinkerLaunch"
            target.mkdir(parents=True)
            marker = target / "preserve.txt"
            marker.write_text("keep")
            result = install_compatibility_tool(home, dry_run=False)
            self.assertFalse(result["ok"])
            self.assertTrue(marker.exists())
            self.assertEqual(marker.read_text(), "keep")

    def test_missing_executable_dry_run_plans_upstream_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam = home / ".local/share/Steam"
            (steam / "steamapps").mkdir(parents=True)
            result = install_compatibility_tool(home, dry_run=True)
            self.assertTrue(result["ok"])
            self.assertTrue(result["dry_run"])
            self.assertEqual(result["install_target"], str(home / "stl/prefix"))
            self.assertFalse((steam / "compatibilitytools.d").exists())

    def test_installs_upstream_source_then_registers_compat_tool(self):
        # Kept as a regression test for the first implementation; helper layout is updated below.

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, _ = self.fixture_home(home)
            source = home / "stl/prefix"
            target = steam / "compatibilitytools.d/SteamTinkerLaunch"
            def fake_run(command, **kwargs):
                if command[1] == "clone":
                    source.mkdir(parents=True)
                    exe = source / "steamtinkerlaunch"
                    exe.write_text("#!/bin/sh\\n")
                    exe.chmod(0o755)
                    return type("Result", (), {"returncode": 0, "stdout": "cloned", "stderr": ""})()
                target.mkdir(parents=True)
                (target / "compatibilitytool.vdf").write_text("test")
                (target / "toolmanifest.vdf").write_text("test")
                return type("Result", (), {"returncode": 0, "stdout": "added", "stderr": ""})()
            with patch("stl_compatibility.subprocess.run", side_effect=fake_run) as run:
                result = install_compatibility_tool(home, dry_run=False)
            self.assertTrue(result["ok"])
            self.assertTrue((source / "steamtinkerlaunch").exists())
            self.assertTrue((target / "toolmanifest.vdf").exists())
            self.assertEqual(run.call_count, 2)

    def test_calls_upstream_add_and_verifies_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, exe = self.fixture_home(home)
            target = steam / "compatibilitytools.d/SteamTinkerLaunch"
            def fake_run(command, **kwargs):
                target.mkdir(parents=True)
                (target / "compatibilitytool.vdf").write_text("test")
                (target / "toolmanifest.vdf").write_text("test")
                return type("Result", (), {"returncode": 0, "stdout": "added", "stderr": ""})()
            with patch("stl_compatibility.subprocess.run", side_effect=fake_run) as run:
                result = install_compatibility_tool(home, dry_run=False)
            self.assertTrue(result["ok"])
            run.assert_called_once()
            self.assertEqual(run.call_args.args[0][-2:], ["compat", "add"])
            self.assertTrue((target / "compatibilitytool.vdf").exists())
            self.assertTrue((target / "toolmanifest.vdf").exists())

if __name__ == "__main__":
    unittest.main()
