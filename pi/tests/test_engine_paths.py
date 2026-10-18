"""Engine routing contract smoke; does not substitute for running an engine."""
import tempfile
import unittest
from pathlib import Path

from pi.runtime.config import PACKAGE_ROOT, resolve
from pi.runtime.init_game import initialize


class EngineRoutingTests(unittest.TestCase):
    def test_setup_engine_pi_skill_never_directs_writes_into_shared_framework(self):
        skill = (PACKAGE_ROOT / "pi/skills/setup-engine/SKILL.md").read_text()
        self.assertIn("game's `project.yaml`", skill)
        self.assertIn("docs/technical-preferences.md", skill)
        self.assertIn("NOT VERIFIED", skill)
        self.assertIn("Never update the framework's `CLAUDE.md`", skill)
        self.assertIn("references/11-upgrade.md", skill)
        self.assertIn("project-coherence", skill)

    def test_three_engines_resolve_from_game_and_have_bundled_reference_and_role(self):
        for engine in ("Godot", "Unity", "Unreal"):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                initialize(root, "Concept", "standard", "collaborative")
                with (root / "project.yaml").open("a") as out:
                    out.write(f"\nengine:\n  name: {engine}\n  version: example-only\n")
                self.assertIn(f"engine: {engine} example-only (project.yaml)", resolve(root, "engine"))
                docs = PACKAGE_ROOT / "docs/engine-reference" / engine.lower()
                for filename in ("VERSION.md", "current-best-practices.md", "breaking-changes.md", "deprecated-apis.md"):
                    self.assertTrue((docs / filename).is_file(), docs / filename)
                self.assertTrue((PACKAGE_ROOT / "pi/skills" / f"ccgs-{engine.lower()}-specialist/SKILL.md").is_file())
                self.assertFalse((root / ".claude").exists())
                self.assertFalse((root / "docs/engine-reference").exists(),
                                 "Reference material remains in the framework until explicitly copied")


if __name__ == "__main__":
    unittest.main()
