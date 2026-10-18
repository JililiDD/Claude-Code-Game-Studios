import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pi.runtime.config import PACKAGE_ROOT, resolve


class ConfigTests(unittest.TestCase):
    def test_game_root_and_local_override_not_framework_config(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("modes:\n  rigor: full\n  automation: collaborative\n")
            (game / "project.local.yaml").write_text("modes:\n  automation: guided\n")
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(PACKAGE_ROOT)}):
                result = resolve(game, "review_mode,automation,workflow")
            self.assertIn("review_mode: full (rigor:full)", result)
            self.assertIn("automation: guided (project.local.yaml)", result)
            self.assertIn("workflow: full (rigor:full)", result)

    def test_bare_single_and_pair_resolutions_are_accepted_not_discarded(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text(
                "schema_version: 1\nengine:\n  name: Unity\n  version: 6.3\nmodes:\n  rigor: standard\n")
            self.assertIn("automation: collaborative", resolve(game, "automation"))
            self.assertIn("engine: Unity 6.3", resolve(game, "engine"))
            self.assertIn("workflow: standard", resolve(game, "automation, workflow"))
            self.assertIn("=== CCGS Resolved Config ===", resolve(game))
            with self.assertRaisesRegex(ValueError, "Unsupported config keys"):
                resolve(game, "engine.name")

    def test_bad_config_and_invalid_enum_are_labeled_instead_of_accepted_as_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("modes:\n  automation: impossible\n")
            response = resolve(game, "automation,workflow")
            self.assertIn("automation: collaborative", response)
            self.assertIn("notes:", response)
            self.assertIn("impossible", response)
            (game / "project.yaml").write_text("modes:\n  - bad\n  : [unterminated\n")
            with self.assertRaisesRegex(ValueError, "malformed YAML"):
                resolve(game, "automation")
            (game / "project.yaml").write_text("modes:\n  rigor: full\n  rigor: minimal\n")
            with self.assertRaisesRegex(ValueError, "duplicate YAML key"):
                resolve(game, "rigor")

    def test_uninitialized_game_is_rejected_not_silently_defaulted(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Missing .*project.yaml"):
                resolve(Path(directory))

    def test_framework_checkout_is_not_a_game(self):
        with self.assertRaisesRegex(ValueError, "framework checkout"):
            resolve(PACKAGE_ROOT)


if __name__ == "__main__":
    unittest.main()
