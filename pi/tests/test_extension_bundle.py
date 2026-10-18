import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXTENSIONS = ("studio-guidelines", "studio-rules", "studio-approval", "studio-gates", "studio-checks", "studio-session")


class ExtensionBundleTests(unittest.TestCase):
    def test_all_six_extensions_load_together_in_game_rpc(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as agent:
            game = Path(directory)
            (game / "project.yaml").write_text("schema_version: 1\nmodes:\n  automation: collaborative\n")
            command = ["pi", "--mode", "rpc", "--no-session", "--no-context-files", "--no-mcp",
                       "--no-extensions", "--no-skills", "--no-themes", "--no-prompt-templates"]
            for name in EXTENSIONS:
                command.extend(["--extension", str(ROOT / "pi/extensions" / (name + ".ts"))])
            run = subprocess.run(command, cwd=game, input=json.dumps({"id": "status", "type": "get_state"}) + "\n",
                                 capture_output=True, text=True, timeout=40,
                                 env={**os.environ, "PI_CODING_AGENT_DIR": agent, "PI_OFFLINE": "1"})
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertNotIn("extension error", run.stderr.lower())
            self.assertTrue(json.loads(run.stdout.splitlines()[0])["success"])
            self.assertFalse((game / "production/release.md").exists())


if __name__ == "__main__":
    unittest.main()
