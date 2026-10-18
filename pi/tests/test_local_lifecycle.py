"""Model/engine-independent local lifecycle integration for the game-root adapters.

This is not a playable build or a director approval. It verifies that local
helpers can be chained without accidentally treating the package as a game.
"""
import tempfile
import unittest
from pathlib import Path

from pi.runtime.artifacts import PACKAGE_ROOT, check
from pi.runtime.config import resolve
from pi.runtime.init_game import initialize
from pi.runtime.scripts import observe
from pi.runtime.session import lifecycle
from pi.runtime.stories import status


class LocalLifecycleTests(unittest.TestCase):
    def test_new_game_design_story_qa_release_observations_do_not_mutate_framework(self):
        framework_config = (PACKAGE_ROOT / "project.yaml").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            initialize(game, "Concept", "standard", "collaborative")
            self.assertIn("workflow: standard", resolve(game, "workflow,automation"))
            first = check(game, path="minimal")
            self.assertIn("status=ABSENT", first)
            (game / "design/gdd").mkdir(parents=True)
            (game / "design/game-brief.md").write_text("# Example game\n")
            (game / "design/gdd/combat.md").write_text("## Overview\nBasic combat loop.\n")
            self.assertIn("combat.md PRESENT: Overview", observe(game, "gdd-structure-check").stdout)
            (game / "docs/architecture").mkdir(parents=True)
            self.assertIn("ADRS: 0", observe(game, "adr-dep-graph").stdout)
            stories = game / "production/epics/EPIC-001"
            stories.mkdir(parents=True)
            (stories / "story-1.md").write_text("Status: Ready\n")
            self.assertIn("TODO", status(game))
            self.assertIn("PHASE: concept", check(game, all_phases=True))
            (game / "tests/unit").mkdir(parents=True)
            (game / "tests/unit/test_combat.md").write_text("# Placeholder; not a passing game test\n")
            self.assertIn("ROOT: " + str(game), check(game, path="minimal"))
            start = lifecycle(game, "start", "game.jsonl")
            self.assertEqual(start.returncode, 0, start.stderr)
            self.assertEqual(lifecycle(game, "settled", "game.jsonl").returncode, 0)
            self.assertFalse((game / "production/release-approved.md").exists())
            self.assertEqual((PACKAGE_ROOT / "project.yaml").read_bytes(), framework_config)

    def test_existing_game_with_local_override_and_unverified_reference_is_not_approved(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text(
                "schema_version: 1\nproject:\n  stage: Technical Setup\n"
                "modes:\n  rigor: full\n  automation: collaborative\n"
                "engine:\n  name: Unreal\n  version: 5.8\n")
            (game / "project.local.yaml").write_text("modes:\n  automation: guided\n")
            self.assertIn("automation: guided (project.local.yaml)", resolve(game, "automation,workflow"))
            report = observe(game, "project-coherence")
            self.assertEqual(report.returncode, 0, report.stderr)
            self.assertIn("[NOT CHECKED]", report.stdout)
            self.assertIn("no readable Engine/Build/Build.version", report.stdout)
            self.assertFalse((game / "docs/engine-reference/unreal/VERSION.md").exists())
            self.assertNotIn("[MATCH]       engine.version", report.stdout)


if __name__ == "__main__":
    unittest.main()
