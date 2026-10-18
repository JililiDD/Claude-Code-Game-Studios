"""Smoke every workflow skill's Pi command expansion with a local mock model.

This checks routing/availability and does not prove the model follows each
workflow's phase contracts; game lifecycle acceptance is a separate gate.
"""
import http.server
import json
import os
import queue
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = sorted(path.parent.name for path in (ROOT / ".claude/skills").glob("*/SKILL.md"))


class ExpansionProvider(http.server.BaseHTTPRequestHandler):
    seen = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.seen.append(request)
        message = {"id": "skill", "object": "chat.completion.chunk", "model": request["model"],
                   "choices": [{"index": 0, "delta": {"role": "assistant", "content": "Loaded workflow."},
                                "finish_reason": None}]}
        stop = {"id": "skill", "object": "chat.completion.chunk", "model": request["model"],
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for chunk in (message, stop):
            self.wfile.write(b"data: " + json.dumps(chunk).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


class WorkflowFleetTests(unittest.TestCase):
    def test_every_74_workflow_skill_expands_in_a_separate_game(self):
        self.assertEqual(len(WORKFLOWS), 74)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = root / "game"
            game.mkdir()
            (game / "project.yaml").write_text("schema_version: 1\n")
            agent = root / "agent"
            agent.mkdir()
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ExpansionProvider)
            ExpansionProvider.seen = []
            threading.Thread(target=server.serve_forever, daemon=True).start()
            (agent / "models.json").write_text(json.dumps({"providers": {"local-test": {
                "api": "openai-completions", "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
                "apiKey": "offline", "models": [{"id": "workflow-model"}]}}}))
            command = ["pi", "--mode", "rpc", "--no-session", "--no-context-files", "--no-mcp",
                       "--no-extensions", "--no-skills", "--no-themes", "--no-prompt-templates",
                       "--model", "local-test/workflow-model", "--skill", str(ROOT / "pi/skills")]
            process = subprocess.Popen(command, cwd=game,
                                       env={**os.environ, "PI_CODING_AGENT_DIR": str(agent), "PI_OFFLINE": "1"},
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, bufsize=1)
            rows = queue.Queue()
            threading.Thread(target=lambda: [rows.put(json.loads(line)) for line in process.stdout], daemon=True).start()
            try:
                process.stdin.write(json.dumps({"id": "disable-compaction", "type": "set_auto_compaction", "enabled": False}) + "\n")
                process.stdin.flush()
                config = rows.get(timeout=20)
                self.assertTrue(config.get("success"), config)
                for name in WORKFLOWS:
                    process.stdin.write(json.dumps({"id": name, "type": "prompt", "message": f"/skill:{name}"}) + "\n")
                    process.stdin.flush()
                    answered = False
                    for _ in range(45):
                        try:
                            event = rows.get(timeout=20)
                        except queue.Empty:
                            process.kill()
                            process.wait(timeout=5)
                            self.fail(f"{name} skill did not complete; stderr={process.stderr.read()}")
                        if event.get("id") == name and event.get("type") == "response":
                            self.assertTrue(event["success"], f"{name}: {event}")
                            answered = True
                        if event.get("type") == "agent_settled":
                            break
                    else:
                        self.fail(f"{name}: no agent_settled")
                    self.assertTrue(answered, name)
                    self.assertEqual(len(ExpansionProvider.seen), WORKFLOWS.index(name) + 1, name)
                    submitted = str(ExpansionProvider.seen[-1]["messages"])
                    self.assertIn(f'<skill name="{name}"', submitted, name)
                    self.assertIn(f"/pi/skills/{name}/SKILL.md", submitted, name)
                    self.assertEqual(ExpansionProvider.seen[-1]["model"], "workflow-model")
            finally:
                process.stdin.close()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                server.shutdown()
                server.server_close()
                process.stdout.close()
                error = process.stderr.read()
                process.stderr.close()
            self.assertEqual(process.returncode, 0, error)
            self.assertEqual(len(ExpansionProvider.seen), 74)
            self.assertEqual(set(game.iterdir()), {game / "project.yaml"},
                             "A skill invocation alone must not write game files")


if __name__ == "__main__":
    unittest.main()
