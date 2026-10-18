# Owner validation checklist — NOT YET PASSED

This is the handoff **after** local implementation work (steps 1–3). It does
not assert a usable release. Run `python3 pi/migration/local_check.py` first.
The local suite uses mock models and does not substitute for these tests.

## Safe temporary Pi invocation

Work from a **separate disposable game root**, never the framework checkout.
Install Python 3 + PyYAML. Point to the absolute framework checkout path
(`FRAMEWORK` below); this does not install resources globally or modify your
Pi settings. Run Pi with your own currently selected model (do not force a
Claude model):

```bash
FRAMEWORK=/absolute/path/to/Claude-Code-Game-Studios
pi --no-context-files --skill "$FRAMEWORK/pi/skills" \
  -e "$FRAMEWORK/pi/extensions/studio-guidelines.ts" \
  -e "$FRAMEWORK/pi/extensions/studio-rules.ts" \
  -e "$FRAMEWORK/pi/extensions/studio-approval.ts" \
  -e "$FRAMEWORK/pi/extensions/studio-gates.ts" \
  -e "$FRAMEWORK/pi/extensions/studio-checks.ts" \
  -e "$FRAMEWORK/pi/extensions/studio-session.ts"
```

`--no-context-files` avoids accidentally importing a game-local Claude Code
`CLAUDE.md` during Pi testing. Check `/skill:help` and `/skill:start` are
available. Generated skills still say *draft*: the root `package.json` does
not expose them, so this command is a **validation fixture**, not a release
or install recipe. Inspect every proposed game file before approving a write;
the approval extension cannot sandbox arbitrary shell scripts.

## 4. Lifecycle and engine acceptance (owner)

- **Fresh game**: initialize with `/skill:start` in a clean game repository;
  select rigor and automation, verify only game `project.yaml` and
  `production/stage.txt` changed. Walk brainstorm/brief → engine setup →
  system design → architecture/ADR → epic/story → implementation → QA and
  evidence → release preparation. At every transition record the invoked
  skill, role/gate tool result, output path and verdict; missing evidence must
  remain NOT ASSESSED. Do not simulate native engine results.
- **Existing game**: preserve its code, comments, local overrides and state.
  Exercise `/skill:project-stage-detect`, `/skill:adopt`, and a read-only v1
  migration preview. If relevant, approve migration and finalization **as
  separate decisions**. Run session restart/compaction and compare checkpoint
  recovery to `production/session-state/active.md`.
- **Three engine projects**: configure Godot, Unity and Unreal separately.
  Verify actual executable/version, game-owned pinned `VERSION.md`, project
  files, engine-specific source root and a native build/test. On Godot, the
  approved parse-check script is staged at `addons/ccgs_pi/`; running its
  CLI alone is NOT a Godot run. Observe player-visible changes and retain
  screenshots in `production/qa/evidence/` before closing stories. Where an
  engine is unavailable, record NOT VERIFIED and do not approve release.
- **Negative paths**: missing prerequisite, declined new-file approval,
  invalid YAML, blocked/NOT ASSESSED gate, failing build/test, missing screenshot,
  interruption and resumption. No workflow may silently skip a blocker or
  claim a different role's independent review.

## 5. Model, packaging and compatibility acceptance (owner)

- Run critical design, implementation/review and QA/release stages on **two
  actual Pi models from different providers**. Switch models in one game
  mid-project and verify the same game `project.yaml`, roles and gates are
  used without changing model pins. A mock HTTP model is not this test.
- Verify Claude Code still loads original `.claude/` skills and hooks, and
  its default scripts still target the Claude game. Pi must not write to
  shared framework assets. Check package installation, upgrade and removal
  in a disposable Pi agent directory, confirming game files are unchanged.
- Only after per-resource evidence and these owner checks pass, update
  `pi/migration/contracts.json` with **real evidence** and enable the package
  entry points in `package.json`. Then run
  `python3 pi/migration/contracts.py --release` and inspect every gate result.
  A failing release command or any NOT VERIFIED engine/model result blocks
  publication. Commit/push and publish only after separate authorization.
