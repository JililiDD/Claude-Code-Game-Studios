import json
import re
import subprocess
import unittest
from pathlib import Path

from pi.migration.behavior_matrix import ROOT, build
from pi.migration.generate_candidates import MANUAL, check_preprocessing
from pi.runtime.role import load as load_role


class BehaviorMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = build()["resources"]
        cls.contracts = json.loads((ROOT / "pi/migration/contracts.json").read_text())

    def test_all_source_resources_have_real_pi_disposition_and_source_hash(self):
        for kind, expected in (("skills", 74), ("agents", 49), ("hooks", 14), ("rules", 13)):
            with self.subTest(kind=kind):
                self.assertEqual(len(self.matrix[kind]), expected)
                self.assertEqual(set(self.matrix[kind]), set(self.contracts[kind]))
                for source, item in self.matrix[kind].items():
                    with self.subTest(source=source):
                        self.assertEqual(len(item["source_sha256"]), 64)
                        self.assertEqual(item["target"], self.contracts[kind][source]["target"])
                        state = self.contracts[kind][source]["state"]
                        self.assertNotEqual(state, "pending", source)
                        if state != "inapplicable":
                            self.assertTrue((ROOT / item["target"]).is_file(), source)
                        elif kind == "hooks":
                            self.assertTrue(self.contracts[kind][source]["note"], source)

    def test_every_workflow_reference_link_resolves_inside_its_bundled_skill(self):
        for source, item in self.matrix["skills"].items():
            skill_dir = (ROOT / source).parent
            for markdown in [ROOT / source, *(ROOT / path for path in item["source_reference_files"])]:
                for link in re.findall(r"(?<![\\w./])references/[\\w./-]+\\.md", markdown.read_text()):
                    with self.subTest(markdown=markdown.name, link=link):
                        target = (skill_dir / link).resolve()
                        self.assertTrue(target.is_relative_to(skill_dir))
                        self.assertTrue(target.is_file(), f"{markdown}: {link}")

    def test_every_workflow_has_a_pi_entry_and_all_preprocessing_is_mapped(self):
        for source, item in self.matrix["skills"].items():
            with self.subTest(source=source):
                name = Path(source).parent.name
                target = ROOT / item["target"]
                body = target.read_text()
                self.assertIn(f"name: {name}\n", body)
                self.assertNotIn("model: sonnet", body)
                check_preprocessing(name, (ROOT / source).read_text())
                self.assertEqual(bool(item["preprocessing"]),
                                 "!`" in (ROOT / source).read_text().split("\n---\n", 1)[1])
                for ref in item["source_reference_files"]:
                    self.assertTrue((ROOT / ref).is_file(), ref)
                for gate in item["named_director_gates"]:
                    self.assertTrue((ROOT / ".claude/docs/director-gates" / f"{gate.lower()}.md").is_file(),
                                    f"{source} requires missing gate {gate}")
                if name not in MANUAL:
                    self.assertIn("ccgs_gate_review", body)
                    self.assertIn("ccgs_role_consult", body)
                    self.assertIn("game root", body.lower())
                    self.assertIn("NOT ASSESSED", body)

    def test_each_role_loads_body_and_has_named_entry_and_safe_failure(self):
        for source, item in self.matrix["agents"].items():
            role = Path(source).stem
            with self.subTest(role=role):
                body = load_role(role)
                self.assertTrue(body.strip())
                entry = (ROOT / item["target"]).read_text()
                self.assertIn(f"name: ccgs-{role}", entry)
                self.assertIn("ccgs-role", entry)
                self.assertIn("ccgs_role_consult", entry)
                self.assertIn("NOT ASSESSED", entry)
        with self.assertRaisesRegex(ValueError, "Unknown CCGS role"):
            load_role("../project.yaml")

    def test_all_rule_patterns_are_actual_scoped_sources(self):
        for source, item in self.matrix["rules"].items():
            with self.subTest(source=source):
                self.assertTrue(item["path_patterns"])
                self.assertEqual(item["target"], "pi/extensions/studio-rules.ts")

    def test_matrix_is_drift_checked(self):
        run = subprocess.run(["python3", str(ROOT / "pi/migration/behavior_matrix.py"), "--check"],
                             capture_output=True, text=True, cwd=ROOT, timeout=15)
        self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":
    unittest.main()
