"""Exercise every named role's fresh Pi tool invocation with an offline model.

This is structural execution evidence, NOT a real-model quality or game lifecycle
verdict. No role is allowed to write an output file.
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
ROLES = sorted(path.stem for path in (ROOT / ".claude/agents").glob("*.md"))


class RoleProvider(http.server.BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.calls.append(data)
        messages = data["messages"]
        first = str(messages[0].get("content", ""))
        if "fresh read-only Pi model request" in first:
            role = first.split("You are the CCGS ", 1)[1].split(" in a fresh", 1)[0]
            delta = {"role": "assistant", "content": f"UNSAVED DRAFT FOR {role}"}
            finish = "stop"
        elif messages[-1].get("role") == "tool":
            delta = {"role": "assistant", "content": "Role consultations collected; writing requires approval."}
            finish = "stop"
        else:
            calls = []
            for index, role in enumerate(ROLES):
                calls.append({"index": index, "id": f"role-{index}", "type": "function",
                              "function": {"name": "ccgs_role_consult", "arguments": json.dumps({
                                  "role": role, "context": f"Analyze the game brief as {role}",
                                  "files": ["design/brief.md"]})}})
            delta = {"role": "assistant", "tool_calls": calls}
            finish = "tool_calls"
        chunks = [
            {"id": "roles", "object": "chat.completion.chunk", "model": data["model"],
             "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
            {"id": "roles", "object": "chat.completion.chunk", "model": data["model"],
             "choices": [{"index": 0, "delta": {}, "finish_reason": finish}]},
        ]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for chunk in chunks:
            self.wfile.write(b"data: " + json.dumps(chunk).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


class RoleFleetTests(unittest.TestCase):
    def test_all_49_roles_have_fresh_read_only_pi_invocations(self):
        self.assertEqual(len(ROLES), 49)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = root / "game"
            (game / "design").mkdir(parents=True)
            (game / "project.yaml").write_text("schema_version: 1\n")
            (game / "design/brief.md").write_text("An invented game for offline port tests.\n")
            agent = root / "pi-agent"
            agent.mkdir()
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RoleProvider)
            RoleProvider.calls = []
            threading.Thread(target=server.serve_forever, daemon=True).start()
            (agent / "models.json").write_text(json.dumps({"providers": {"ccgs-test": {
                "baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "api": "openai-completions",
                "apiKey": "offline", "models": [{"id": "game-model"}]}}}))
            env = {**os.environ, "PI_CODING_AGENT_DIR": str(agent), "PI_OFFLINE": "1"}
            command = ["pi", "--mode", "rpc", "--no-session", "--no-context-files", "--no-mcp",
                       "--no-extensions", "--no-skills", "--no-themes", "--no-prompt-templates",
                       "--provider", "ccgs-test", "--model", "game-model", "--extension",
                       str(ROOT / "pi/extensions/studio-gates.ts")]
            process = subprocess.Popen(command, cwd=game, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            rows = queue.Queue()
            threading.Thread(target=lambda: [rows.put(json.loads(line)) for line in process.stdout], daemon=True).start()
            events = []
            try:
                process.stdin.write(json.dumps({"type": "prompt", "message": "Consult all 49 roles"}) + "\n")
                process.stdin.flush()
                for _ in range(1000):
                    try:
                        event = rows.get(timeout=45)
                    except queue.Empty:
                        process.kill()
                        process.wait(timeout=5)
                        self.fail(f"Fleet stalled after {len(events)} events; stderr={process.stderr.read()}")
                    if event.get("type") == "tool_execution_end":
                        events.append(event)
                    if event.get("type") == "agent_settled":
                        break
                else:
                    self.fail("Fleet did not settle")
            finally:
                process.stdin.close()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                server.shutdown()
                server.server_close()
                process.stdout.close()
                errors = process.stderr.read()
                process.stderr.close()
            self.assertEqual(process.returncode, 0, errors)
            self.assertEqual(len(events), 49, str(events)[:1800])
            for role in ROLES:
                self.assertIn(f"UNSAVED DRAFT FOR {role}", str(events))
            audit = (game / "production/session-logs/agent-audit.log").read_text()
            self.assertEqual(audit.count("Role invoked:"), 49)
            self.assertEqual(audit.count("Role completed:"), 49)
            self.assertTrue(all(request["model"] == "game-model" for request in RoleProvider.calls))
            self.assertEqual(list(game.rglob("*.md")), [game / "design/brief.md"])


if __name__ == "__main__":
    unittest.main()
