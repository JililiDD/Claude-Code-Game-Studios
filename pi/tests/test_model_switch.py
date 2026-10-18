"""Offline Pi RPC smoke with two configured, local mock model IDs.

This verifies model selection and guideline delivery, not quality of a real LLM.
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


class MockProvider(http.server.BaseHTTPRequestHandler):
    calls = []
    review = False
    gate_verdict = "APPROVE"

    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length))
        self.calls.append(data)
        model = data["model"]
        if self.review == "role" and "You are the CCGS game-designer" in str(data.get("messages", [])):
            delta = {"role": "assistant", "content": "DRAFT: one-page concept with a clear fantasy."}
            finish = "stop"
        elif self.review and "fresh, read-only CCGS review" in str(data.get("messages", [])):
            delta = {"role": "assistant", "content": f"CD-PILLARS: {self.gate_verdict}\nMock pillar evidence reviewed."}
            finish = "stop"
        elif self.review and data.get("messages", [{}])[-1].get("role") == "tool":
            delta = {"role": "assistant", "content": "Review tool returned."}
            finish = "stop"
        elif self.review:
            if self.review == "role":
                name = "ccgs_role_consult"
                args = {"role": "game-designer", "context": "Draft a one-page concept", "files": ["design/game-brief.md"]}
            else:
                name = "ccgs_gate_review"
                args = {"gate": "cd-pillars", "context": "Fantasy, comparable, pillars and anti-pillars supplied",
                        "files": ["design/game-brief.md"]}
            delta = {"role": "assistant", "tool_calls": [{"index": 0, "id": "review-1", "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)}}]}
            finish = "tool_calls"
        else:
            delta = {"role": "assistant", "content": f"MOCK {model}"}
            finish = "stop"
        chunks = [
            {"id": "test", "object": "chat.completion.chunk", "model": model,
             "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
            {"id": "test", "object": "chat.completion.chunk", "model": model,
             "choices": [{"index": 0, "delta": {}, "finish_reason": finish}]},
        ]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for chunk in chunks:
            self.wfile.write(b"data: " + json.dumps(chunk).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


class ModelSwitchTests(unittest.TestCase):
    def test_selected_pi_model_can_change_during_same_game_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = root / "game"
            game.mkdir()
            (game / "project.yaml").write_text("schema_version: 1\n")
            agent = root / "pi-agent"
            agent.mkdir()
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), MockProvider)
            MockProvider.calls = []
            MockProvider.review = False
            MockProvider.gate_verdict = "APPROVE"
            serving = threading.Thread(target=server.serve_forever, daemon=True)
            serving.start()
            (agent / "models.json").write_text(json.dumps({"providers": {"ccgs-test": {
                "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
                "api": "openai-completions", "apiKey": "offline",
                "models": [{"id": "model-a"}, {"id": "model-b"}],
            }}}))
            env = {**os.environ, "PI_CODING_AGENT_DIR": str(agent), "PI_OFFLINE": "1"}
            cmd = ["pi", "--mode", "rpc", "--no-session", "--no-context-files", "--no-mcp",
                   "--no-extensions", "--no-skills", "--no-themes", "--no-prompt-templates",
                   "--provider", "ccgs-test", "--model", "model-a", "--extension",
                   str(ROOT / "pi/extensions/studio-guidelines.ts")]
            process = subprocess.Popen(cmd, cwd=game, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            rows = queue.Queue()
            threading.Thread(target=lambda: [rows.put(json.loads(line)) for line in process.stdout], daemon=True).start()
            try:
                for model in ("model-a", "model-b"):
                    if model == "model-b":
                        process.stdin.write(json.dumps({"id": "switch", "type": "set_model",
                                                        "provider": "ccgs-test", "modelId": model}) + "\n")
                        process.stdin.flush()
                        reply = rows.get(timeout=20)
                        self.assertTrue(reply["success"], reply)
                    process.stdin.write(json.dumps({"id": model, "type": "prompt", "message": "Say hello"}) + "\n")
                    process.stdin.flush()
                    events = []
                    for _ in range(100):
                        try:
                            row = rows.get(timeout=20)
                        except queue.Empty:
                            process.kill()
                            process.wait(timeout=5)
                            self.fail(f"Pi emitted no event; prior={events}; stderr={process.stderr.read()}")
                        events.append(row)
                        if row.get("type") == "agent_settled":
                            break
                    else:
                        self.fail("Pi session did not settle")
                    self.assertTrue(any(row.get("id") == model and row.get("success") for row in events), events)
                    self.assertTrue(any("MOCK " + model in str(row) for row in events), events)
                self.assertEqual([request["model"] for request in MockProvider.calls], ["model-a", "model-b"])
                for request in MockProvider.calls:
                    prompt = str(request["messages"])
                    self.assertIn("CCGS for Pi", prompt)
                    self.assertIn("a parse check is not a run", prompt.lower())
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
                process.stderr.close()
            self.assertEqual(process.returncode, 0)

    def test_director_gate_uses_current_model_in_fresh_request(self):
        self._review_case(False)

    def test_not_assessed_gate_is_never_counted_as_approval(self):
        self._review_case(False, gate_verdict="NOT ASSESSED")

    def test_invalid_gate_verdict_does_not_become_approval(self):
        self._review_case(False, gate_verdict="NONSENSE")

    def test_role_draft_is_unsaved_and_uses_current_model(self):
        self._review_case(True)

    def test_audit_log_symlink_cannot_escape_game_root(self):
        self._review_case(False, audit_symlink=True)

    def test_symlinked_game_evidence_cannot_escape_game_root(self):
        self._review_case(False, escape_evidence=True)

    def _review_case(self, role_draft, audit_symlink=False, gate_verdict="APPROVE", escape_evidence=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = root / "game"
            (game / "design").mkdir(parents=True)
            (game / "project.yaml").write_text("schema_version: 1\n")
            (game / "design/game-brief.md").write_text(
                "Fantasy: guide a lost crew. Pillars: scarce resources, mutual aid. "
                "Anti-pillars: no grind. Hook: survival AND solidarity.\n")
            if audit_symlink:
                canary = root / "outside-canary"
                canary.write_text("untouched")
                logs = game / "production/session-logs"
                logs.mkdir(parents=True)
                (logs / "agent-audit.log").symlink_to(canary)
            agent = root / "pi-agent"
            agent.mkdir()
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), MockProvider)
            MockProvider.calls = []
            MockProvider.review = "role" if role_draft else True
            MockProvider.gate_verdict = gate_verdict
            threading.Thread(target=server.serve_forever, daemon=True).start()
            (agent / "models.json").write_text(json.dumps({"providers": {"ccgs-test": {
                "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
                "api": "openai-completions", "apiKey": "offline",
                "models": [{"id": "model-a"}, {"id": "model-b"}],
            }}}))
            env = {**os.environ, "PI_CODING_AGENT_DIR": str(agent), "PI_OFFLINE": "1"}
            cmd = ["pi", "--mode", "rpc", "--no-session", "--no-context-files", "--no-mcp",
                   "--no-extensions", "--no-skills", "--no-themes", "--no-prompt-templates",
                   "--provider", "ccgs-test", "--model", "model-b", "--extension",
                   str(ROOT / "pi/extensions/studio-gates.ts")]
            process = subprocess.Popen(cmd, cwd=game, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            rows = queue.Queue()
            threading.Thread(target=lambda: [rows.put(json.loads(line)) for line in process.stdout], daemon=True).start()
            events = []
            try:
                process.stdin.write(json.dumps({"type": "prompt", "message": "Draft the concept" if role_draft else "Run the CD pillars gate"}) + "\n")
                process.stdin.flush()
                for _ in range(100):
                    try:
                        event = rows.get(timeout=20)
                    except queue.Empty:
                        process.kill()
                        process.wait(timeout=5)
                        self.fail(f"Gate run stalled: {events}; stderr={process.stderr.read()}")
                    events.append(event)
                    if event.get("type") == "agent_settled":
                        break
                else:
                    self.fail("Gate run did not settle")
                expected = "Unsaved game-designer draft" if role_draft else f"CD-PILLARS: {gate_verdict}"
                if gate_verdict == "NONSENSE":
                    self.assertIn("Review returned invalid verdict", str(events))
                    self.assertNotIn("Review APPROVE", str(events))
                else:
                    self.assertIn(expected, str(events))
                calls_with_evidence = len(MockProvider.calls)
                (game / "design/game-brief.md").unlink()
                if escape_evidence:
                    private = root / "private.md"
                    private.write_text("Never send private data to the model\n")
                    (game / "design/game-brief.md").symlink_to(private)
                process.stdin.write(json.dumps({"type": "prompt", "message": "Draft the concept again" if role_draft else "Run the CD pillars gate again"}) + "\n")
                process.stdin.flush()
                failed_events = []
                for _ in range(100):
                    failed = rows.get(timeout=20)
                    failed_events.append(failed)
                    if failed.get("type") == "agent_settled":
                        break
                else:
                    self.fail("Missing-evidence gate run did not settle")
                self.assertIn("outside the game project" if escape_evidence else "game-brief.md", str(failed_events))
                if escape_evidence:
                    self.assertNotIn("Never send private data", str(MockProvider.calls))
                self.assertNotIn(expected, str(failed_events))
                self.assertEqual(len(MockProvider.calls), calls_with_evidence + 2,
                                 "Missing game evidence must not start an independent review")
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
            self.assertIn("ccgs_role_consult" if role_draft else "ccgs_gate_review", str(events))
            if gate_verdict != "NONSENSE":
                self.assertIn(expected, str(events))
            self.assertGreaterEqual(len(MockProvider.calls), 3)
            self.assertTrue(all(request["model"] == "model-b" for request in MockProvider.calls))
            audit = (game / "production/session-logs/agent-audit.log").read_text()
            if audit_symlink:
                self.assertEqual(audit, "untouched")
                return
            if role_draft:
                self.assertIn("Role invoked: game-designer", audit)
                self.assertIn("Role completed: game-designer", audit)
                self.assertFalse((game / "production/concept.md").exists())
            else:
                self.assertIn("Review invoked: creative-director", audit)
                if gate_verdict == "NONSENSE":
                    self.assertIn("Review invalid: creative-director", audit)
                else:
                    self.assertIn(f"Review {gate_verdict}: creative-director", audit)


if __name__ == "__main__":
    unittest.main()
