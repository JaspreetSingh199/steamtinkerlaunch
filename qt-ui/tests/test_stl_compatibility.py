import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from stl_compatibility import (compatibility_tool_targets, find_stl_executable, install_compatibility_tool, inspect_compatibility_tool, reset_stl_steam)

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

    def test_verified_existing_compatibility_tool_is_reported_as_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, _ = self.fixture_home(home)
            target = steam / "compatibilitytools.d/SteamTinkerLaunch"
            target.mkdir(parents=True)
            (target / "compatibilitytool.vdf").write_text("owned")
            (target / "toolmanifest.vdf").write_text("owned")
            result = install_compatibility_tool(home, dry_run=False)
            self.assertTrue(result["ok"])
            self.assertTrue(result["already_installed"])
            self.assertEqual(result["existing"], [str(target)])

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
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, local_exe = self.fixture_home(home)
            local_exe.unlink()  # force the test through the upstream clone path
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
            self.assertEqual(run.call_args_list[0].args[0][1], "clone")
            self.assertEqual(run.call_args_list[1].args[0][-2:], ["compat", "add"])

    def test_reset_dry_run_reports_scope_and_does_not_modify(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, _ = self.fixture_home(home)
            install = home / ".local/share/stl-steam"
            install.mkdir(parents=True, exist_ok=True)
            (install / "marker.txt").write_text("keep")
            link = steam / "compatibilitytools.d/SteamTinkerLaunch"
            link.parent.mkdir(parents=True)
            link.symlink_to(install, target_is_directory=True)
            result = reset_stl_steam(home, dry_run=True)
            self.assertTrue(result["ok"])
            self.assertTrue((install / "marker.txt").exists())
            self.assertTrue(link.is_symlink())
            self.assertIn("MO2 installations", " ".join(result["preserved"]))

    def test_reset_backs_up_app_and_removes_only_compat_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, _ = self.fixture_home(home)
            install = home / ".local/share/stl-steam"
            install.mkdir(parents=True, exist_ok=True)
            (install / "marker.txt").write_text("keep")
            target = steam / "compatibilitytools.d/SteamTinkerLaunch"
            target.parent.mkdir(parents=True)
            target.symlink_to(install, target_is_directory=True)
            config = home / ".config/steamtinkerlaunch/gamecfgs/id/489830.conf"
            config.parent.mkdir(parents=True)
            config.write_text("MO2MODE=gui")
            result = reset_stl_steam(home, dry_run=False)
            self.assertTrue(result["ok"])
            self.assertFalse(install.exists())
            self.assertTrue(Path(result["backup"]).is_dir())
            self.assertTrue((Path(result["backup"]) / "marker.txt").exists())
            self.assertFalse(target.is_symlink())
            self.assertEqual(config.read_text(), "MO2MODE=gui")

    def test_reset_backups_verified_real_compatibility_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, _ = self.fixture_home(home)
            install = home / ".local/share/stl-steam"
            install.mkdir(parents=True, exist_ok=True)
            target = steam / "compatibilitytools.d/SteamTinkerLaunch"
            target.mkdir(parents=True)
            (target / "compatibilitytool.vdf").write_text("owned marker")
            (target / "toolmanifest.vdf").write_text("owned marker")
            marker = target / "preserve.txt"
            marker.write_text("preserve")
            result = reset_stl_steam(home, dry_run=False)
            self.assertTrue(result["ok"], result.get("message"))
            self.assertFalse(target.exists())
            backup_target = Path(result["compatibility_backups"][0])
            self.assertTrue((backup_target / "preserve.txt").exists())
            self.assertEqual((backup_target / "preserve.txt").read_text(), "preserve")

    def test_reset_refuses_unverified_real_compatibility_directory_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, _ = self.fixture_home(home)
            install = home / ".local/share/stl-steam"
            install.mkdir(parents=True, exist_ok=True)
            (install / "app-marker").write_text("keep")
            target = steam / "compatibilitytools.d/SteamTinkerLaunch"
            target.mkdir(parents=True)
            marker = target / "keep"
            marker.write_text("preserve")
            result = reset_stl_steam(home, dry_run=False)
            self.assertFalse(result["ok"])
            self.assertTrue(install.exists(), "preflight must not move the app before refusing")
            self.assertTrue(marker.exists())
            self.assertEqual(marker.read_text(), "preserve")
            self.assertFalse(result.get("backup"))

    def test_reset_backs_up_real_compatibility_directory_beside_steam_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam, _ = self.fixture_home(home)
            target = steam / "compatibilitytools.d/SteamTinkerLaunch"
            target.mkdir(parents=True)
            (target / "compatibilitytool.vdf").write_text("owned")
            (target / "toolmanifest.vdf").write_text("owned")
            result = reset_stl_steam(home, dry_run=False)
            self.assertTrue(result["ok"], result)
            backup = Path(result["compatibility_backups"][0])
            self.assertEqual(backup.parent, target.parent)
            self.assertTrue((backup / "toolmanifest.vdf").exists())
            self.assertIn(str(target), result["compatibility_targets"])
            self.assertIn(str(backup), result["compatibility_backups"])
            self.assertIn("Restore each compatibility backup", result["recovery_note"])


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
