import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATES = ROOT / ".claude/docs/director-gates"


class GateTests(unittest.TestCase):
    def test_every_gate_has_existing_role_and_machine_verdicts(self):
        files = sorted(GATES.glob("*.md"))
        self.assertEqual(len(files), 28)
        for path in files:
            with self.subTest(gate=path.name):
                text = path.read_text()
                role = re.search(r"^Agent:\s*`([a-z][a-z0-9-]+)`", text, re.M)
                verdicts = re.search(r"^\*\*Verdicts\*\*:\s*(.*)$", text, re.M)
                self.assertIsNotNone(role)
                self.assertIsNotNone(verdicts)
                self.assertTrue((ROOT / ".claude/agents" / (role[1] + ".md")).is_file())
                self.assertTrue(all(re.match(r"^[A-Z]+(?: [A-Z]+)*", value.strip())
                                    for value in verdicts[1].split(" / ")))

    def test_gate_extension_loads_in_pi_rpc_without_a_model_call(self):
        result = subprocess.run(
            ["pi", "--mode", "rpc", "--no-session", "--no-skills", "--no-context-files",
             "-ne", "-e", str(ROOT / "pi/extensions/studio-gates.ts")],
            input='{"id":"state","type":"get_state"}\n', text=True, capture_output=True,
            cwd=ROOT, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"command":"get_state","success":true', result.stdout)
        self.assertNotIn("extension error", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
