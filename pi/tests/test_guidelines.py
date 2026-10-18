import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class GuidelineTests(unittest.TestCase):
    def test_project_guidelines_are_scoped_and_preserve_evidence_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            script = """
                import register from '__MODULE__';
                const hooks = {};
                register({on: (name, fn) => hooks[name] = fn});
                const evt = () => ({systemPromptOptions:{sections:{}}});
                const without = evt();
                hooks.before_agent_start(without, {cwd: process.argv[2]});
                if (without.systemPromptOptions.sections.ccgs_guidelines) process.exit(1);
                const framework = evt();
                hooks.before_agent_start(framework, {cwd: process.argv[3]});
                if (framework.systemPromptOptions.sections.ccgs_guidelines) process.exit(2);
                const fs = await import('node:fs');
                fs.writeFileSync(process.argv[2] + '/project.yaml', 'schema_version: 1\\n');
                const withProject = evt();
                hooks.before_agent_start(withProject, {cwd: process.argv[2]});
                const text = withProject.systemPromptOptions.sections.ccgs_guidelines || '';
                if (!text.includes('a parse check is not a run') && !text.includes('A parse check is not a run')) process.exit(3);
                if (!text.includes('ccgs_role_consult') || !text.includes('ccgs_gate_review')) process.exit(4);
                if (!text.includes('Retained screenshot') && !text.includes('retained screenshot')) process.exit(5);
            """.replace("__MODULE__", (ROOT / "pi/extensions/studio-guidelines.ts").as_uri())
            run = subprocess.run(["node", "--input-type=module", "-", directory, str(ROOT)],
                                 input=script, text=True, capture_output=True, cwd=ROOT, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":
    unittest.main()
