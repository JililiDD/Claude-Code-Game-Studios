import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PackageSafetyTests(unittest.TestCase):
    def test_no_development_skill_is_exposed_by_package(self):
        manifest = json.loads((ROOT / "package.json").read_text())
        self.assertEqual(manifest["pi"]["skills"], [])
        self.assertEqual(manifest["pi"]["extensions"], [])

    def test_every_source_resource_is_registered(self):
        run = subprocess.run(["python3", str(ROOT / "pi/migration/contracts.py")],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        contracts = json.loads((ROOT / "pi/migration/contracts.json").read_text())
        self.assertEqual(len(contracts["skills"]), 74)
        self.assertTrue(all(v["state"] == "draft" for v in contracts["skills"].values()))
        self.assertEqual(sum(v["state"] == "verified" for v in contracts["skills"].values()), 0)
        for script in ("generate_candidates.py", "generate_roles.py"):
            generated = subprocess.run(["python3", str(ROOT / "pi/migration" / script), "--check"],
                                       cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(generated.returncode, 0, generated.stderr)
        release = subprocess.run(["python3", str(ROOT / "pi/migration/contracts.py"), "--release"],
                                 cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(release.returncode, 0)
        self.assertIn("skills: 74 resources still unverified", release.stderr)

    def test_pi_discovers_all_74_source_skill_candidates(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            env = os.environ.copy()
            env["PI_CODING_AGENT_DIR"] = agent_dir
            run = subprocess.run(
                ["pi", "--mode", "rpc", "--no-session", "--no-context-files", "--no-mcp",
                 "--no-extensions", "--no-skills", "--skill", str(ROOT / "pi/skills")],
                input='{"id":"commands","type":"get_commands"}\n',
                text=True, capture_output=True, cwd=ROOT, env=env, timeout=30,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stderr, "")
            commands = json.loads(run.stdout.strip())["data"]["commands"]
            names = {item["name"] for item in commands if item["source"] == "skill"}
            expected = {"skill:" + path.parent.name for path in (ROOT / ".claude/skills").glob("*/SKILL.md")}
            self.assertTrue(expected.issubset(names))
            roles = {"skill:ccgs-" + path.stem for path in (ROOT / ".claude/agents").glob("*.md")}
            self.assertTrue(roles.issubset(names))
            self.assertEqual(len(names), 125)  # 74 workflows + 49 roles + 2 adapters

    def test_candidates_have_valid_pi_skill_frontmatter(self):
        for path in (ROOT / "pi/skills").glob("*/SKILL.md"):
            with self.subTest(skill=str(path)):
                content = path.read_text()
                self.assertTrue(content.startswith("---\n"))
                frontmatter = content.split("\n---\n", 1)[0]
                self.assertIn(f"name: {path.parent.name}", frontmatter)
                self.assertIn("description:", frontmatter)
                self.assertNotIn("model:", frontmatter)


if __name__ == "__main__":
    unittest.main()
