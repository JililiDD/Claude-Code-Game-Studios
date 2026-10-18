import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from pi.runtime.checks import PACKAGE_ROOT, validate


class CheckTests(unittest.TestCase):
    def test_asset_json_check_preserves_blocking_exit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("schema_version: 1\n")
            asset = game / "assets/data/item.json"
            asset.parent.mkdir(parents=True)
            asset.write_text('{"valid": true}\n')
            self.assertEqual(validate(game, "assets", file="assets/data/item.json").returncode, 0)
            asset.write_text("{invalid")
            broken = validate(game, "assets", file="assets/data/item.json")
            self.assertEqual(broken.returncode, 2)
            self.assertIn("not valid JSON", broken.stderr)
            with self.assertRaisesRegex(ValueError, "inside the game"):
                validate(game, "assets", file="../outside.json")

    def test_invalid_staged_data_blocks_a_commit_in_a_game_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            (game / "project.yaml").write_text("schema_version: 1\n")
            asset = game / "assets/data/invalid.json"
            asset.parent.mkdir(parents=True)
            asset.write_text("{broken")
            subprocess.run(["git", "-C", directory, "add", "."], check=True)
            outcome = validate(game, "commit", command="git commit -m test")
            self.assertEqual(outcome.returncode, 2)
            self.assertIn("invalid.json is not valid JSON", outcome.stderr)

    def test_push_to_protected_branch_is_advisory_not_an_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            (game / "project.yaml").write_text("schema_version: 1\n")
            result = validate(game, "push", command="git push origin HEAD:main")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Push to protected branch", result.stdout)
            self.assertNotIn("permissionDecision", result.stdout)
            quiet = validate(game, "push", command="git push origin HEAD:feature")
            self.assertEqual(quiet.returncode, 0, quiet.stderr)
            self.assertNotIn("Push to protected branch", quiet.stdout)

    def test_pi_check_events_block_bad_commit_and_report_broken_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            (game / "project.yaml").write_text("schema_version: 1\n")
            asset = game / "assets/data/invalid.json"
            asset.parent.mkdir(parents=True)
            asset.write_text("{broken")
            subprocess.run(["git", "-C", directory, "add", "."], check=True)
            script = """
                import register from '__MODULE__';
                const handlers = {};
                register({on: (name, callback) => handlers[name] = callback});
                const ctx = {cwd: process.argv[2], ui:{notify:()=>{}}};
                const commit = await handlers.tool_call({toolName:'bash',input:{command:'git commit -m test'}},ctx);
                if (!commit?.block || !commit.reason.includes('invalid.json')) process.exit(1);
                const result = await handlers.tool_result({toolName:'write',input:{path:'assets/data/invalid.json'},
                  content:[{type:'text',text:'Written'}],isError:false},ctx);
                if (!result?.isError || !result.content.at(-1).text.includes('AFTER the edit')) process.exit(2);
            """.replace("__MODULE__", (PACKAGE_ROOT / "pi/extensions/studio-checks.ts").as_uri())
            run = subprocess.run(["node", "--input-type=module", "-", directory], input=script,
                                 text=True, capture_output=True, cwd=PACKAGE_ROOT, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_pi_checks_extension_starts_in_rpc(self):
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ.copy()
            env["PI_CODING_AGENT_DIR"] = directory
            root = PACKAGE_ROOT
            run = subprocess.run(
                ["pi", "--mode", "rpc", "--no-session", "--no-skills", "--no-context-files",
                 "-ne", "-e", str(root / "pi/extensions/studio-checks.ts")],
                input=json.dumps({"id": "state", "type": "get_state"}) + "\n",
                text=True, capture_output=True, cwd=root, env=env, timeout=30,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stderr, "")
            self.assertIn('"command":"get_state","success":true', run.stdout)

    def test_framework_cannot_be_validated_as_game(self):
        with self.assertRaisesRegex(ValueError, "outside the framework"):
            validate(PACKAGE_ROOT, "commit", command="git commit")


if __name__ == "__main__":
    unittest.main()
