---
name: gate-check
description: "Ready to advance between development phases? PASS/CONCERNS/NOT ASSESSED/FAIL with blockers and required artifacts. 'Can we move to production?'"
---

# gate-check — Pi migration candidate (NOT verified or released)

The original detailed workflow is bundled at
`<framework-root>/.claude/skills/gate-check/SKILL.md`. Resolve `<framework-root>`
from this skill file's directory by walking `../../..`. **Read the entire
original file and every `references/` file it explicitly directs you to**, from
that source skill directory. Use its domain policy, artifacts, gates, prompts
and error recovery as the contract, with these Pi-specific execution rules:

1. The current working directory is the **game root**, not the installed
   framework. If it is the framework checkout or unclear, stop and ask. Paths
   under `.claude/docs/`, `.claude/scripts/`, `.claude/hooks/`,
   `.claude/agents/` and `.claude/skills/` in the original workflow refer to
   bundled read-only framework assets; `design/`, `docs/`, `production/`,
   engine code roots and `project.yaml` refer to the game. The framework's
   `.claude/docs/technical-preferences.md` is a read-only legacy example:
   prefer game `project.yaml` and then its own legacy
   `.claude/docs/technical-preferences.md` (or `docs/technical-preferences.md`)
   for real engine choices. Never edit the shared fallback or invent a game
   `CLAUDE.md` solely for Pi. Do not edit the framework when the source meant
   to update a game. Resolve source paths with
   `python3 <framework-root>/pi/runtime/code_root.py --project <game-root>`;
   an unresolved root is NOT ASSESSED, not `src/` by default. A source request
   to read game `CLAUDE.md` means: use
   the Pi `studio-guidelines` context plus game `project.yaml`, optional game
   `docs/technical-preferences.md`, and game engine reference; do not demand
   a `CLAUDE.md` file in a separate game. `CLAUDE.md` bundled at framework root
   is Claude-specific and must never be edited from a game.
2. Claude `!` shell interpolation and `CLAUDE_SKILL_DIR` do **not** execute in
   Pi. For `resolve_config --keys X`, explicitly run
   `python3 <framework-root>/pi/runtime/config.py --project <game-root>
   --keys X` and inspect its output. `!` preprocessing for story-status
   maps to `pi/runtime/stories.py`; `git log`, `git tag` and `ls` observations
   run in the game root. Every original `!` expression must pass the
   generator's explicit mapping check. Never treat a missing bootstrap result
   as a default.
3. The original frontmatter `model:`, `tools:`, `allowed-tools:`, `context:`,
   `memory:` and `skills:` configure Claude Code, not Pi. Stay on Pi's current
   model and use only tools actually available. Ask user questions in normal
   conversation and wait for decisions; a suggested choice is not approval.
4. A named role in `.claude/agents/` can be used in the main Pi session via
   `/skill:ccgs-role`. To obtain an independently generated role draft, call
   `ccgs_role_consult` with a bounded brief and evidence; it uses a fresh,
   read-only current-model request and returns an **unsaved** draft. Several
   consultations may run in parallel; the coordinator verifies their actual
   return values, gets write approval and saves artifacts itself. A named
   director gate requires `ccgs_gate_review` with complete evidence and a
   fresh verdict. NOT ASSESSED is not approval. The `TaskCreate`/`TaskGet`/
   `TaskList`/`TaskUpdate` names appear only in Claude frontmatter grants,
   not as required body steps; they do not require a Pi task-board tool.
   Do not launch subagents merely because the Claude source mentions `Agent`.
5. Use the tested game-root wrappers for script observations:
   `pi/runtime/artifacts.py` for catalog artifacts,
   `pi/runtime/stories.py` for ordered stories, and
   `pi/runtime/scripts.py` for GDD structure, project coherence, review
   scope/receipts, and ADR dependency graphs. For Godot parse checks, after
   explicit approval, stage the bundled script with
   `python3 <framework-root>/pi/runtime/godot_check.py --project <game-root>
   --stage --approved`, then request `--command src/<script>.gd` for its
   game-owned `res://addons/ccgs_pi/` path; never run the original
   `res://.claude/scripts/` path in a Pi-only game. This prepares a check,
   NOT engine execution evidence. For v1 adoption, use
   `python3 <framework-root>/pi/runtime/migrate.py --project <game-root>`
   (read-only preview); `--mode migrate --approved` and later
   `--mode finalize --approved` are **two separate user-approved writes**.
   Never finalize merely because migration succeeded. Always pass `--project` with the real game
   root. For any other script that assumes the template is the game root,
   adapt and test it first or stop and report the missing dependency.
   Never run a script against the framework by mistake.
6. Claude `/name` or `Skill(name)` references mean: read and follow
   `<framework-root>/pi/skills/name/SKILL.md` in this same Pi session;
   user-entered commands are `/skill:name`. Before chaining, confirm the
   target's state in `<framework-root>/pi/migration/contracts.json`. In a
   **disposable validation fixture only**, a draft dependency may be exercised
   as a test, explicitly marked unverified throughout. In a production game,
   stop if any required dependency is not verified. Do not invent success
   or skip the dependency.
7. Preserve the original artifact, approval and failure contracts. Work on
   game files only after the applicable approval. Do not commit or push unless
   the user asks. State which checks or role passes were not actually run.

## Source-specific handoff inventory for `gate-check`

Read the bundled `CCGS Skill Testing Framework/skills/gate/gate-check.md` for this workflow's named scenarios and failure expectations; the spec is an obligation, not a passed test.

Read the following bundled reference files when the source phase calls for
one; their paths are relative to the **source skill directory**, never the
game. These are search leads, not permission to skip any other cited file:
- `references/2b-workflow-tier.md`
- `references/3-run-gate-check.md`
- `references/4-assessment.md`
- `references/5-verdict.md`
- `references/6-update-stage.md`
- `references/7-next-steps.md`
- `references/gate-polish.md`
- `references/gate-pre-production.md`
- `references/gate-production.md`
- `references/gate-release.md`
- `references/gate-systems-design.md`
- `references/gate-technical-setup.md`

The source mentions these other workflow commands. The Pi invocation form
is listed, but its approval, failure and dependency rules must be checked
before chaining:
- `/skill:architecture-decision`
- `/skill:architecture-review`
- `/skill:art-bible`
- `/skill:asset-spec`
- `/skill:balance-check`
- `/skill:brainstorm`
- `/skill:create-architecture`
- `/skill:create-control-manifest`
- `/skill:create-epics`
- `/skill:create-stories`
- `/skill:design-review`
- `/skill:design-system`
- `/skill:dev-story`
- `/skill:help`
- `/skill:launch-checklist`
- `/skill:localize`
- `/skill:map-systems`
- `/skill:perf-profile`
- `/skill:playtest-report`
- `/skill:project-stage-detect`
- `/skill:prototype`
- `/skill:qa-plan`
- `/skill:quick-design`
- `/skill:release-checklist`
- `/skill:reverse-document`
- `/skill:review-all-gdds`
- `/skill:security-audit`
- `/skill:settings`
- `/skill:setup-engine`
- `/skill:smoke-check`
- `/skill:sprint-plan`
- `/skill:sprint-status`
- `/skill:story-readiness`
- `/skill:team-qa`
- `/skill:team-ui`
- `/skill:test-setup`
- `/skill:ux-design`
- `/skill:ux-review`
- `/skill:vertical-slice`

Preprocessed source commands that **must be run explicitly** if their phase
is reached (and against the game root):
- `bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys review_mode,workflow,qa.level,testing.strict,performance.enforce,team.size,project.stage,system_overrides`

Named independent director gates in the source or its references, if their
conditions are reached. Each uses complete game evidence and is NOT ASSESSED
until the separate Pi tool result is inspected:
- `AD-ART-BIBLE → ccgs_gate_review ad-art-bible`
- `AD-PHASE-GATE → ccgs_gate_review ad-phase-gate`
- `CD-PHASE-GATE → ccgs_gate_review cd-phase-gate`
- `PR-PHASE-GATE → ccgs_gate_review pr-phase-gate`
- `TD-PHASE-GATE → ccgs_gate_review td-phase-gate`

Additional source-specific Pi translation:
- No additional source-only shell calls were identified; follow the full bundled workflow.

This candidate intentionally stays out of the package manifest until its
individual behavior and dependencies have been tested. It does not certify
that `gate-check` works end-to-end in Pi.
