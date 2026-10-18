import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RuleTests(unittest.TestCase):
    def test_all_scoped_rules_have_matching_patterns_and_usable_engine_paths(self):
        rules = list((ROOT / ".claude/rules").glob("*.md"))
        self.assertEqual(len(rules), 13)
        for rule in rules:
            with self.subTest(rule=rule.name):
                text = rule.read_text()
                self.assertTrue(text.startswith("---\npaths:\n"))
        run = subprocess.run(["node", "-e", """
            const {matchesGlob} = require('node:path');
            const cases = [
              ['src/gameplay/character.gd','src/gameplay/**'],
              ['Assets/X/Gameplay/Character.cs','Assets/**/{Gameplay,gameplay}/**/*.cs'],
              ['Source/X/Gameplay/Character.cpp','Source/**/{Gameplay,gameplay}/**/*.{h,cpp}'],
            ];
            if (cases.some(([path,glob]) => !matchesGlob(path,glob))) process.exit(1);
        """], capture_output=True, text=True, timeout=15)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_each_of_13_rule_bodies_is_served_for_an_actual_matching_game_path(self):
        paths = {
            "agent-memory.md": ".claude/agent-memory/notes.md",
            "ai-code.md": "src/ai/enemy.gd",
            "data-files.md": "assets/data/loot/table.json",
            "design-docs.md": "design/gdd/movement.md",
            "engine-code.md": "src/core/main.gd",
            "gameplay-code.md": "src/gameplay/character.gd",
            "narrative.md": "design/narrative/chapter.md",
            "network-code.md": "src/networking/transport.gd",
            "prototype-code.md": "prototypes/jump.gd",
            "shader-code.md": "assets/shaders/glow.gdshader",
            "skill-authoring.md": ".claude/skills/local/SKILL.md",
            "test-standards.md": "tests/unit/test_moves.gd",
            "ui-code.md": "src/ui/hud.gd",
        }
        self.assertEqual(set(paths), {file.name for file in (ROOT / ".claude/rules").glob("*.md")})
        with tempfile.TemporaryDirectory() as game:
            (Path(game) / "project.yaml").write_text("schema_version: 1\n")
            script = """
                import register from '__MODULE__';
                const handlers = {};
                register({on: (name, handler) => handlers[name] = handler});
                const ctx = {cwd:process.argv[2]};
                for (const [name,path] of Object.entries(JSON.parse(process.argv[3]))) {
                  handlers.before_agent_start({messageType:'user',systemPromptOptions:{sections:{}}},ctx);
                  const first = handlers.tool_call({toolName:'write',input:{path}},ctx);
                  if (!first?.block || !first.reason.includes('## ' + name)) {
                    console.error(name,path,first);process.exit(1);
                  }
                  const second = handlers.tool_call({toolName:'write',input:{path}},ctx);
                  if (second?.block) process.exit(2);
                }
            """.replace("__MODULE__", (ROOT / "pi/extensions/studio-rules.ts").as_uri())
            run = subprocess.run(["node", "--input-type=module", "-", game, json.dumps(paths)],
                                 input=script, text=True, capture_output=True, cwd=ROOT, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_unconfigured_new_game_still_blocks_writes_outside_its_root(self):
        with tempfile.TemporaryDirectory() as game:
            script = """
              import register from '__MODULE__';
              const handlers = {};
              register({on:(name,fn)=>handlers[name]=fn});
              const ctx = {cwd:process.argv[2]};
              const outcome = handlers.tool_call({toolName:'write',
                input:{path:process.argv[3]+'/CLAUDE.md'}},ctx);
              if (!outcome?.block) process.exit(1);
              const config = handlers.tool_call({toolName:'write',
                input:{path:'project.yaml'}},ctx);
              if (config?.block) process.exit(2);
            """.replace("__MODULE__", (ROOT / "pi/extensions/studio-rules.ts").as_uri())
            run = subprocess.run(["node", "--input-type=module", "-", game, str(ROOT)],
                                 input=script, text=True, capture_output=True, cwd=ROOT, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_matching_edit_receives_rule_before_retry(self):
        with tempfile.TemporaryDirectory() as game:
            (Path(game) / "project.yaml").write_text("schema_version: 1\n")
            module = (ROOT / "pi/extensions/studio-rules.ts").as_uri()
            program = """
                import register from '__MODULE__';
                const handlers = {};
                register({on: (name, handler) => { handlers[name] = handler; }});
                const ctx = {cwd: process.argv[2]};
                const event = {messageType: 'user', systemPromptOptions:{sections:{}}};
                handlers.before_agent_start(event, ctx);
                if (!event.systemPromptOptions.sections.ccgs_rules) process.exit(1);
                const request = {toolName:'edit', input:{path:'src/gameplay/test.gd'}};
                const first = handlers.tool_call(request, ctx);
                if (!first?.block || !first.reason.includes('Gameplay Code Rules')) process.exit(2);
                if (handlers.tool_call(request, ctx)) process.exit(3);
                handlers.before_agent_start(event, ctx);
                if (!handlers.tool_call(request, ctx)?.block) process.exit(4);
                const outside = {toolName:'write',input:{path:process.argv[3] + '/CLAUDE.md'}};
                if (!handlers.tool_call(outside, ctx)?.block) process.exit(5);
                const fs = await import('node:fs');
                fs.symlinkSync(process.argv[3], process.argv[2] + '/external');
                const symlink = {toolName:'write',input:{path:'external/CLAUDE.md'}};
                if (!handlers.tool_call(symlink, ctx)?.block) process.exit(6);
            """.replace("__MODULE__", module)
            run = subprocess.run(["node", "--input-type=module", "-", game, str(ROOT)],
                                 input=program, text=True, capture_output=True, cwd=ROOT, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_rules_extension_starts_without_user_config(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            env = os.environ.copy()
            env["PI_CODING_AGENT_DIR"] = agent_dir
            run = subprocess.run(
                ["pi", "--mode", "rpc", "--no-session", "--no-skills", "--no-context-files",
                 "-ne", "-e", str(ROOT / "pi/extensions/studio-rules.ts")],
                input=json.dumps({"id": "state", "type": "get_state"}) + "\n",
                text=True, capture_output=True, cwd=ROOT, env=env, timeout=30,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stderr, "")
            self.assertIn('"command":"get_state","success":true', run.stdout)


if __name__ == "__main__":
    unittest.main()
