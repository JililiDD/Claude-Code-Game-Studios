"""End-to-end Pi RPC rejection: dismissed dialog does not create the file."""
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


class Writer(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if request["messages"][-1].get("role") == "tool":
            delta = {"role": "assistant", "content": "The user declined; no file written."}
            finish = "stop"
        else:
            delta = {"role": "assistant", "tool_calls": [{"index": 0, "id": "write-1", "type": "function",
                "function": {"name": "write", "arguments": json.dumps({"path": "draft.md", "content": "Draft\n"})}}]}
            finish = "tool_calls"
        chunks = [
            {"id": "w", "object": "chat.completion.chunk", "model": request["model"],
             "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
            {"id": "w", "object": "chat.completion.chunk", "model": request["model"],
             "choices": [{"index": 0, "delta": {}, "finish_reason": finish}]},
        ]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for item in chunks:
            self.wfile.write(b"data: " + json.dumps(item).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


class ApprovalRPCTests(unittest.TestCase):
    def test_cancelled_user_confirmation_blocks_model_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = root / "game"
            game.mkdir()
            (game / "project.yaml").write_text("schema_version: 1\nmodes:\n  automation: collaborative\n")
            agent = root / "agent"
            agent.mkdir()
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Writer)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            (agent / "models.json").write_text(json.dumps({"providers": {"local-test": {
                "api": "openai-completions", "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
                "apiKey": "offline", "models": [{"id": "writer"}]}}}))
            process = subprocess.Popen(
                ["pi", "--mode", "rpc", "--no-session", "--no-context-files", "--no-mcp",
                 "--no-extensions", "--no-skills", "--no-themes", "--no-prompt-templates",
                 "--model", "local-test/writer", "--extension", str(ROOT / "pi/extensions/studio-approval.ts")],
                cwd=game, env={**os.environ, "PI_CODING_AGENT_DIR": str(agent), "PI_OFFLINE": "1"},
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            rows = queue.Queue()
            threading.Thread(target=lambda: [rows.put(json.loads(line)) for line in process.stdout], daemon=True).start()
            got_confirm = False
            got_blocked = False
            try:
                process.stdin.write(json.dumps({"type": "prompt", "message": "Propose a draft"}) + "\n")
                process.stdin.flush()
                for _ in range(100):
                    try:
                        row = rows.get(timeout=20)
                    except queue.Empty:
                        process.kill()
                        process.wait(timeout=5)
                        self.fail(f"Pi write dialog stalled; stderr={process.stderr.read()}")
                    if row.get("type") == "extension_ui_request" and row.get("method") == "confirm":
                        got_confirm = True
                        self.assertIn("draft.md", row["message"])
                        process.stdin.write(json.dumps({"type": "extension_ui_response", "id": row["id"],
                                                        "cancelled": True}) + "\n")
                        process.stdin.flush()
                    if row.get("type") == "tool_execution_end":
                        got_blocked = "not approved" in str(row)
                    if row.get("type") == "agent_settled":
                        break
                else:
                    self.fail("Pi did not settle after cancellation")
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
                error = process.stderr.read()
                process.stderr.close()
            self.assertEqual(process.returncode, 0, error)
            self.assertTrue(got_confirm)
            self.assertTrue(got_blocked)
            self.assertFalse((game / "draft.md").exists())


if __name__ == "__main__":
    unittest.main()
