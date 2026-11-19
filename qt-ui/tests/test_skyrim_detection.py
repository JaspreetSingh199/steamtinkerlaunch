import tempfile
import unittest
from pathlib import Path
from skyrim_detection import detect_skyrim, _parse_vdf_paths

class DetectionTests(unittest.TestCase):
    def test_parse_vdf_path(self):
        self.assertEqual(_parse_vdf_paths('"path" "/mnt/games"'), ["/mnt/games"])

    def test_no_steam_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(detect_skyrim(Path(tmp))["found"])

    def test_default_library_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam = home / ".local/share/Steam"
            game = steam / "steamapps/common/Skyrim Special Edition"
            game.mkdir(parents=True)
            (steam / "steamapps/appmanifest_489830.acf").write_text('"installdir" "Skyrim Special Edition"')
            result = detect_skyrim(home)
            self.assertTrue(result["found"])
            self.assertEqual(Path(result["game_dir"]), game.resolve())

    def test_alternate_library_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steam = home / ".steam/steam"
            steamapps = steam / "steamapps"
            steamapps.mkdir(parents=True)
            alternate = home / "Games/SteamLibrary"
            game = alternate / "steamapps/common/Skyrim Special Edition"
            game.mkdir(parents=True)
            (steamapps / "libraryfolders.vdf").write_text(f'"path" "{steam}"\n"path" "{alternate}"')
            (alternate / "steamapps/appmanifest_489830.acf").write_text('"installdir" "Skyrim Special Edition"')
            result = detect_skyrim(home)
            self.assertTrue(result["found"])
            self.assertEqual(Path(result["game_dir"]), game.resolve())

if __name__ == "__main__":
    unittest.main()
