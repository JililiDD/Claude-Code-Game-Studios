"""Offline runtime contract test for every bundled director gate; no real model judgement."""
import http.server
import json
import os
import queue
import re
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATES = sorted(path.stem for path in (ROOT / ".claude/docs/director-gates").glob("*.md"))


class GateProvider(http.server.BaseHTTPRequestHandler):
    reviews = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        messages = data["messages"]
        system = str(messages[0].get("content", ""))
        if "fresh, read-only CCGS review" in system:
            match = re.search(r"first output line MUST be ([A-Z0-9-]+): <one of ([^,]+)", system)
            if not match:
                raise AssertionError("Review prompt lacked the gate's verdict contract")
            gate, verdict = match.group(1), match.group(2).split(" / ")[0]
            self.reviews.append(gate)
            delta = {"role": "assistant", "content": f"{gate}: {verdict}\nMock evidence noted."}
            finish = "stop"
        elif messages[-1].get("role") == "tool":
            delta = {"role": "assistant", "content": "All mock gate results collected; no game artifact changed."}
            finish = "stop"
        else:
            delta = {"role": "assistant", "tool_calls": [
                {"index": index, "id": f"gate-{index}", "type": "function",
                 "function": {"name": "ccgs_gate_review", "arguments": json.dumps({
                     "gate": gate, "context": f"Review {gate} against this fixture; unavailable real data is NOT ASSESSED.",
                     "files": ["design/brief.md"]})}}
                for index, gate in enumerate(GATES)]}
            finish = "tool_calls"
        chunks = [
            {"id": "gates", "object": "chat.completion.chunk", "model": data["model"],
             "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
            {"id": "gates", "object": "chat.completion.chunk", "model": data["model"],
             "choices": [{"index": 0, "delta": {}, "finish_reason": finish}]},
        ]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for chunk in chunks:
            self.wfile.write(b"data: " + json.dumps(chunk).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


class GateFleetTests(unittest.TestCase):
    def test_every_gate_can_execute_with_a_model_and_explicit_game_evidence(self):
        self.assertEqual(len(GATES), 28)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = root / "game"
            (game / "design").mkdir(parents=True)
            (game / "project.yaml").write_text("schema_version: 1\n")
            (game / "design/brief.md").write_text("Invented game fixture.\n")
            agent = root / "pi-agent"
            agent.mkdir()
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), GateProvider)
            GateProvider.reviews = []
            threading.Thread(target=server.serve_forever, daemon=True).start()
            (agent / "models.json").write_text(json.dumps({"providers": {"ccgs-test": {
                "baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "api": "openai-completions",
                "apiKey": "offline", "models": [{"id": "gate-model"}]}}}))
            env = {**os.environ, "PI_CODING_AGENT_DIR": str(agent), "PI_OFFLINE": "1"}
            command = ["pi", "--mode", "rpc", "--no-session", "--no-context-files", "--no-mcp",
                       "--no-extensions", "--no-skills", "--no-themes", "--no-prompt-templates",
                       "--provider", "ccgs-test", "--model", "gate-model", "--extension",
                       str(ROOT / "pi/extensions/studio-gates.ts")]
            process = subprocess.Popen(command, cwd=game, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            rows = queue.Queue()
            threading.Thread(target=lambda: [rows.put(json.loads(line)) for line in process.stdout], daemon=True).start()
            events = []
            try:
                process.stdin.write(json.dumps({"type": "prompt", "message": "Run 28 mock gates"}) + "\n")
                process.stdin.flush()
                for _ in range(800):
                    try:
                        event = rows.get(timeout=45)
                    except queue.Empty:
                        process.kill()
                        process.wait(timeout=5)
                        self.fail(f"Gate fleet stalled: {events[-2:]}; stderr={process.stderr.read()}")
                    if event.get("type") == "tool_execution_end":
                        events.append(event)
                    if event.get("type") == "agent_settled":
                        break
                else:
                    self.fail("Gate fleet did not settle")
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
            self.assertEqual(len(events), 28, str(events)[:1800])
            self.assertEqual(sorted(GateProvider.reviews), [gate.upper() for gate in GATES])
            audit = (game / "production/session-logs/agent-audit.log").read_text()
            self.assertEqual(audit.count("Review invoked:"), 28)
            self.assertTrue(all("Review " in line for line in audit.splitlines() if "Review invoked:" not in line))
            self.assertFalse((game / "production/release.md").exists())


if __name__ == "__main__":
    unittest.main()
