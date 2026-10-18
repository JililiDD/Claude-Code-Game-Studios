import tempfile
import unittest
from pathlib import Path

from pi.runtime.artifacts import PACKAGE_ROOT, check


class ArtifactTests(unittest.TestCase):
    def test_catalog_from_package_scans_only_the_game(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("engine:\n  name: Godot\n")
            result = check(game, path="minimal")
            self.assertIn(f"ROOT: {game}", result)
            self.assertIn("PATH: minimal", result)
            self.assertIn("STEP: game-brief", result)
            self.assertIn("status=ABSENT", result)
            (game / "design").mkdir()
            (game / "design/game-brief.md").write_text("# Brief\n")
            self.assertIn("STEP: game-brief", check(game, path="minimal"))
            self.assertIn("PHASE: concept", check(game, all_phases=True))

    def test_reject_framework_and_missing_selection(self):
        with self.assertRaisesRegex(ValueError, "outside the framework"):
            check(PACKAGE_ROOT, path="minimal")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Exactly one"):
                check(Path(directory))


if __name__ == "__main__":
    unittest.main()
