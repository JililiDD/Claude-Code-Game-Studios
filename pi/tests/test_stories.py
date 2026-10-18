import tempfile
import unittest
from pathlib import Path

from pi.runtime.stories import PACKAGE_ROOT, status


class StoryTests(unittest.TestCase):
    def test_separate_game_stories_are_prioritized(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            folder = game / "production/epics/first"
            folder.mkdir(parents=True)
            (folder / "story-1.md").write_text("Status: Ready\n")
            (folder / "story-2.md").write_text("Status: In Review\n")
            lines = status(game).splitlines()
            self.assertTrue(lines[0].startswith("IN_REVIEW"))
            self.assertTrue(lines[1].startswith("TODO"))
            self.assertEqual(lines[-1], "COMPLETE     0 of 2")

    def test_framework_checkout_is_not_game(self):
        with self.assertRaisesRegex(ValueError, "outside the framework"):
            status(PACKAGE_ROOT)


if __name__ == "__main__":
    unittest.main()
