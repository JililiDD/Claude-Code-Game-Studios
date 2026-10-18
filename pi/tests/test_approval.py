"""Write-approval negative paths, including dismissed prompts and mode changes."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ApprovalTests(unittest.TestCase):
    def test_rejection_blocks_writes_without_affecting_game_files(self):
        for setting, expected in (("collaborative", [True, True, True]),
                                  ("guided", [False, True, True]),
                                  ("autonomous", [False, False, True])):
            with self.subTest(setting=setting), tempfile.TemporaryDirectory() as directory:
                game = Path(directory)
                (game / "project.yaml").write_text(
                    f"schema_version: 1\nmodes:\n  automation: {setting}\n")
                (game / "old.md").write_text("keep")
                script = """
                    import register from '__MODULE__';
                    const handlers = {};
                    register({on:(name,fn)=>handlers[name]=fn});
                    const asked = [];
                    const ctx = {cwd:process.argv[2],ui:{confirm:async (title,detail)=>{
                      asked.push([title,detail]);return false;
                    }}};
                    const events = [
                      {toolName:'edit',input:{path:'old.md',oldText:'keep',newText:'change'}},
                      {toolName:'write',input:{path:'new.md',content:'draft'}},
                      {toolName:'edit',input:{path:'project.yaml',oldText:'x',newText:'y'}},
                    ];
                    const expected = JSON.parse(process.argv[3]);
                    for (let i=0;i<events.length;i++) {
                      const result = await handlers.tool_call(events[i],ctx);
                      if (!!result?.block !== expected[i]) process.exit(i+1);
                    }
                    if (asked.length !== expected.filter(Boolean).length) process.exit(5);
                    if (asked.some(([_,detail])=>!detail.includes('May I'))) process.exit(6);
                    for (const command of ['git commit -m check','git -C . commit -m check',
                                          'git push origin main','python3 /pkg/pi/runtime/init_game.py --project game',
                                          'bash /pkg/.claude/scripts/migrate-v1-config.sh --finalize']) {
                      const denied = await handlers.tool_call({toolName:'bash',input:{command}},ctx);
                      if (!denied?.block) process.exit(7);
                    }
                """.replace("__MODULE__", (ROOT / "pi/extensions/studio-approval.ts").as_uri())
                run = subprocess.run(["node", "--input-type=module", "-", directory, json.dumps(expected)],
                                     input=script, text=True, capture_output=True, cwd=ROOT, timeout=30)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual((game / "old.md").read_text(), "keep")
                self.assertFalse((game / "new.md").exists())

    def test_invalid_automation_enum_does_not_silently_use_default_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("modes:\n  automation: unrecognized\n")
            script = """
              import register from '__MODULE__';
              const handlers = {};
              register({on:(name,fn)=>handlers[name]=fn});
              const outcome = await handlers.tool_call({toolName:'write',input:{path:'new.md',content:'bad'}},
                {cwd:process.argv[2],ui:{confirm:async()=>true}});
              if (!outcome?.block || !outcome.reason.includes('failed closed')) process.exit(1);
            """.replace("__MODULE__", (ROOT / "pi/extensions/studio-approval.ts").as_uri())
            run = subprocess.run(["node", "--input-type=module", "-", directory], input=script,
                                 text=True, capture_output=True, cwd=ROOT, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_broken_config_never_grants_silent_autonomous_write(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("modes:\n  automation: [broken\n")
            script = """
              import register from '__MODULE__';
              const handlers = {};
              register({on:(name,fn)=>handlers[name]=fn});
              const outcome = await handlers.tool_call({toolName:'write',input:{path:'new.md',content:'bad'}},
                {cwd:process.argv[2],ui:{confirm:async()=>true}});
              if (!outcome?.block || !outcome.reason.includes('failed closed')) process.exit(1);
            """.replace("__MODULE__", (ROOT / "pi/extensions/studio-approval.ts").as_uri())
            run = subprocess.run(["node", "--input-type=module", "-", directory], input=script,
                                 text=True, capture_output=True, cwd=ROOT, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":
    unittest.main()
