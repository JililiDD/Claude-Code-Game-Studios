import tempfile
import unittest
from pathlib import Path

from pi.runtime.config import resolve
from pi.runtime.init_game import PACKAGE_ROOT, initialize


class InitGameTests(unittest.TestCase):
    def test_fresh_game_uses_rigor_without_pinning_fronted_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            initialize(game, "Concept", "standard", "guided")
            content = (game / "project.yaml").read_text(encoding="utf-8")
            self.assertIn("  rigor: standard", content)
            self.assertNotIn("review_mode:", content)
            self.assertEqual((game / "production/stage.txt").read_text(), "Concept")
            resolved = resolve(game, "workflow,review_mode,automation")
            self.assertIn("workflow: standard (rigor:standard)", resolved)
            self.assertIn("review_mode: lean (rigor:standard)", resolved)
            self.assertIn("automation: guided (project.yaml)", resolved)
            with self.assertRaises(FileExistsError):
                initialize(game, "Concept", "full", "autonomous")
            self.assertEqual((game / "project.yaml").read_text(), content)

    def test_reject_framework_root_and_existing_stage_mirror(self):
        with self.assertRaisesRegex(ValueError, "outside the framework"):
            initialize(PACKAGE_ROOT, "Concept", "minimal", "collaborative")
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "production").mkdir()
            (game / "production/stage.txt").write_text("Existing")
            with self.assertRaises(FileExistsError):
                initialize(game, "Concept", "minimal", "collaborative")
            self.assertFalse((game / "project.yaml").exists())


if __name__ == "__main__":
    unittest.main()
