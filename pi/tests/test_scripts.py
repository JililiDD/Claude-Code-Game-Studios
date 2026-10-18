import tempfile
import unittest
from pathlib import Path

from pi.runtime.scripts import FRAMEWORK, observe


class ScriptTests(unittest.TestCase):
    def test_gdd_and_adr_observers_use_game_not_framework(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            gdd = game / "design/gdd/test.md"
            gdd.parent.mkdir(parents=True)
            gdd.write_text("## Overview\n")
            result = observe(game, "gdd-structure-check")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("test.md PRESENT: Overview", result.stdout)
            self.assertNotIn("No system GDDs found", result.stdout)
            graph = observe(game, "adr-dep-graph")
            self.assertEqual(graph.returncode, 0, graph.stderr)
            self.assertIn("ADRS: 0", graph.stdout)
            with self.assertRaisesRegex(ValueError, "game-relative"):
                observe(game, "gdd-structure-check", ("../../outside.md",))
            outside = game.parent / "external.md"
            outside.write_text("secret\n")
            (game / "indirect.md").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "escapes game root"):
                observe(game, "review-receipts", ("hash", "indirect.md"))

    def test_failed_observation_remains_failure_not_clean_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            result = observe(Path(directory), "review-receipts", ("hash", "missing.md"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no such file", result.stderr)
            self.assertNotIn("Reviewed-Content-Hash:", result.stdout)

    def test_framework_and_unsafe_script_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside the framework"):
            observe(FRAMEWORK, "review-scope")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Not an allowed"):
                observe(Path(directory), "migrate-v1-config")


if __name__ == "__main__":
    unittest.main()
