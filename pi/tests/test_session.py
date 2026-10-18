import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from pi.runtime.session import FRAMEWORK, lifecycle


class SessionTests(unittest.TestCase):
    def test_start_reads_game_config_and_checkpoint_then_settled_archives_once(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("schema_version: 1\nmodes:\n  rigor: full\n")
            active = game / "production/session-state/active.md"
            active.parent.mkdir(parents=True)
            active.write_text("<!-- CHECKPOINT -->\nNext: test\n<!-- /CHECKPOINT -->\n")
            start = lifecycle(game, "start")
            self.assertEqual(start.returncode, 0, start.stderr)
            self.assertIn("Review mode: full", start.stdout)
            self.assertIn("Next: test", start.stdout)
            self.assertEqual(lifecycle(game, "settled", "test").returncode, 0)
            report = game / "production/session-logs/session-log.md"
            self.assertIn("Next: test", report.read_text())
            baseline = report.read_text()
            lifecycle(game, "settled", "test")
            self.assertEqual(report.read_text(), baseline)
            self.assertTrue(active.exists())

    def test_pre_and_post_compact_use_game_state_and_remain_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("schema_version: 1\nmodes:\n  rigor: full\n")
            active = game / "production/session-state/active.md"
            active.parent.mkdir(parents=True)
            active.write_text("<!-- CHECKPOINT -->\nNext: recover\n<!-- /CHECKPOINT -->\n" + "Detail\n" * 200)
            pre = lifecycle(game, "pre-compact", "compaction-test")
            self.assertEqual(pre.returncode, 0, pre.stderr)
            self.assertIn("Next: recover", pre.stdout)
            self.assertLess(len(pre.stdout), 5000, "Compaction must not dump the full checkpoint file")
            post = lifecycle(game, "post-compact", "compaction-test")
            self.assertEqual(post.returncode, 0, post.stderr)
            self.assertIn("production/session-state/active.md", post.stdout)
            self.assertNotIn("Detail", post.stdout)
            self.assertTrue(active.exists())

    def test_claude_default_session_cost_keeps_subagent_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("schema_version: 1\n")
            logs = game / "production/session-logs"
            logs.mkdir(parents=True)
            (logs / "agent-audit.log").write_text(
                "2026-01-01 | claude-id | Agent invoked: gameplay-programmer\n")
            env = {**os.environ, "CLAUDE_PROJECT_DIR": directory}
            env.pop("CCGS_INTERFACE", None)
            run = subprocess.run(["bash", str(FRAMEWORK / ".claude/hooks/session-stop.sh")],
                                 input='{"session_id":"claude-id"}', text=True, capture_output=True,
                                 cwd=game, env=env, timeout=20)
            self.assertEqual(run.returncode, 0, run.stderr)
            report = (logs / "session-cost.md").read_text()
            self.assertIn("# Session Subagent Cost", report)
            self.assertIn("Subagent spawns this session: **1**", report)

    def test_pi_role_request_count_is_reported_from_audit_log(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("schema_version: 1\n")
            logs = game / "production/session-logs"
            logs.mkdir(parents=True)
            (logs / "agent-audit.log").write_text(
                "2026-01-01 | game.jsonl | Role invoked: game-designer\n"
                "2026-01-01 | game.jsonl | Role completed: game-designer\n"
                "2026-01-01 | other.jsonl | Review invoked: creative-director\n")
            result = lifecycle(game, "settled", "/private/path/game.jsonl")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = (logs / "session-cost.md").read_text()
            self.assertIn("Fresh Pi model requests this session: **1**", report)
            self.assertIn("| game-designer | 1 |", report)
            self.assertNotIn("creative-director", report)

    def test_session_context_activates_after_start_creates_project_config(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            script = """
                import register from '__MODULE__';
                import {writeFileSync} from 'node:fs';
                const handlers = {};
                register({on: (name, callback) => handlers[name] = callback});
                const ctx = {cwd: process.argv[2], sessionManager:{getSessionFile:()=>''},ui:{notify:()=>{}}};
                await handlers.session_start({reason:'startup'},ctx);
                const before = {systemPromptOptions:{sections:{}}};
                await handlers.before_agent_start(before,ctx);
                if (before.systemPromptOptions.sections.ccgs_session) process.exit(1);
                writeFileSync(process.argv[2] + '/project.yaml','schema_version: 1\\nmodes:\\n  rigor: full\\n');
                const after = {systemPromptOptions:{sections:{}}};
                await handlers.before_agent_start(after,ctx);
                if (!after.systemPromptOptions.sections.ccgs_session?.includes('Review mode: full')) process.exit(2);
                await handlers.agent_settled({},ctx);
            """.replace("__MODULE__", (FRAMEWORK / "pi/extensions/studio-session.ts").as_uri())
            run = subprocess.run(["node", "--input-type=module", "-", directory], input=script,
                                 text=True, capture_output=True, cwd=FRAMEWORK, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_session_events_inject_game_checkpoint_and_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("schema_version: 1\nmodes:\n  rigor: full\n")
            active = game / "production/session-state/active.md"
            active.parent.mkdir(parents=True)
            active.write_text("<!-- CHECKPOINT -->\nNext: gameplay\n<!-- /CHECKPOINT -->\n")
            script = """
                import register from '__MODULE__';
                const handlers = {};
                register({on: (name, callback) => handlers[name] = callback});
                const ctx = {cwd: process.argv[2], sessionManager:{getSessionFile:()=>''},ui:{notify:()=>{}}};
                await handlers.session_start({reason:'startup'},ctx);
                const event = {systemPromptOptions:{sections:{}}};
                await handlers.before_agent_start(event,ctx);
                const text = event.systemPromptOptions.sections.ccgs_session ?? '';
                if (!text.includes('Review mode: full') || !text.includes('Next: gameplay')) process.exit(1);
                await handlers.agent_settled({},ctx);
            """.replace("__MODULE__", (FRAMEWORK / "pi/extensions/studio-session.ts").as_uri())
            run = subprocess.run(["node", "--input-type=module", "-", directory], input=script,
                                 text=True, capture_output=True, cwd=FRAMEWORK, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("Next: gameplay", (game / "production/session-logs/session-log.md").read_text())

    def test_session_extension_loads_for_isolated_game(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as agent_dir:
            game = Path(directory)
            (game / "project.yaml").write_text("schema_version: 1\n")
            env = os.environ.copy()
            env["PI_CODING_AGENT_DIR"] = agent_dir
            run = subprocess.run(
                ["pi", "--mode", "rpc", "--no-session", "--no-skills", "--no-context-files",
                 "-ne", "-e", str(FRAMEWORK / "pi/extensions/studio-session.ts")],
                input=json.dumps({"id": "state", "type": "get_state"}) + "\n",
                cwd=game, text=True, capture_output=True, env=env, timeout=40,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stderr, "")
            self.assertIn('"command":"get_state","success":true', run.stdout)


if __name__ == "__main__":
    unittest.main()
