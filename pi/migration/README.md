# Pi full-port work plan (development branch)

**Status: NOT INSTALLABLE / NOT RELEASED.** This branch is for the complete Pi
port. Do not use an unfinished adapter to develop a game. Keep the existing
`.claude/` tree working until the full Pi release gate is met.

## Scope and source of truth

- `python3 pi/migration/audit.py` records the source inventory in
  `inventory.json`; `--check` detects drift. Flags and slash references are
  search leads, **not** proof that a workflow has been ported.
- `python3 pi/migration/contracts.py` checks that every source resource has a
  disposition in `contracts.json`. `draft` means a candidate exists, **not**
  that it has been validated; `verified` requires its own behavioral tests.
  `generate_candidates.py` scaffolds all 74 Pi workflows and
  `generate_roles.py` scaffolds 49 named role skills without modifying their
  Claude counterparts. The candidate role reader at `pi/skills/ccgs-role/`
  does not confer an independent or verified review on any role. Fresh,
  read-only role drafting and director gates are both candidates in
  `pi/extensions/studio-gates.ts`; the main Pi session alone writes approved
  artifacts. Independent role/gate requests write a bounded audit trail. An
  offline Pi RPC test switches between two mock model IDs and executes a
  fresh gate and an unsaved role draft, including missing-evidence failures;
  it does not prove any real model's review quality. Three engine routing
  fixtures resolve Godot, Unity and Unreal configurations and reference
  assets, but no actual engine binary has yet been run. The resolver checks
  both terse 1–2-key and banner-form output, requires PyYAML for strict
  duplicate-key/malformed-file detection, and rejects unsupported keys
  instead of silently producing missing settings.
- Every one of the 74 skills, 49 roles, 14 hook scripts (including helpers),
  and 13 path-scoped rules needs an explicit disposition: port, share, replace,
  or document why it is inapplicable. Count release coverage by verified
  contracts, not by copied Markdown files.
- `behavior-matrix.json` records source/reference hashes, referenced
  assets/workflows, preprocessing, named gates and test specs for each resource;
  `behavior_matrix.py --check` fails on drift or unexpected missing assets.
  `settings` has no source test spec; its Pi read/validation paths have
  separate tests in `pi/tests/test_settings.py`. Matrix flags are searchable
  obligations, **not** model-behavior verdicts. `local_evidence.py --check`
  assigns each applicable registry entry bounded offline test-file evidence;
  these fields do not change the `draft` state or satisfy the release gate.
- For each skill record inputs, referenced skills and files, approval points,
  role dispatch, required outputs, gates, failure behavior, and tests. Preserve
  the `project.yaml` config semantics (including local overrides and rigor),
  without treating the installed package's repository as the game project.

## Architecture

1. Keep `.claude/` and `CLAUDE.md` for Claude Code. Pi resources live under
   `pi/` and the eventual package manifest selects only Pi-compatible files.
   The original `.claude/skills` must **never** be exposed directly as Pi skills.
2. Shared read-only framework assets live in the installed package; each game
   owns its `project.yaml`, local overrides, code, designs, production state and
   tests. All commands operate on the explicit/current game root, not on the
   installed package checkout. Provide a deliberate initialization/adoption
   path for games. Avoid a project-root `CLAUDE.md` in Pi-only game projects:
   Pi loads that file as context too, and the original mandates Claude tools.
3. Use Pi's current model, not `model: sonnet/opus/haiku`. Switching `/model`
   changes the executor, never the workflow contract or project files. Shared
   `artifact-check.sh` and `story-status.sh` now accept optional Pi game-root
   overrides; their original Claude Code defaults remain unchanged.
4. Adapt Claude's `!` preprocessing to explicit config reads with error
   reporting; `${CLAUDE_SKILL_DIR}` and `.claude/` references to package asset
   resolution; `AskUserQuestion` to visible interactive decisions; `Agent`
   to a role contract. An independent verdict may be claimed only when a
   separately executed review actually took place and was inspected. A
   single-session role pass is explicitly labeled as such.
5. Port path-scoped rules through Pi extension events (candidate:
   `pi/extensions/studio-rules.ts`); a matching first edit/write is blocked
   with the full rule text before retry. Commit/push and post-write asset
   checks are candidates in `pi/extensions/studio-checks.ts`, and session
   recovery/archiving in `pi/extensions/studio-session.ts`. A separate
   `studio-approval.ts` extension tests rejected/dismissed approvals for Pi
   write/edit and high-risk shell commands; this is not a security sandbox
   for arbitrary bash, and no approval is implied by a generated wrapper. Map
   outcomes (blocking / advisory / inapplicable), not just filenames. Pi
   project trust and Claude's `permissions.deny` are not equivalent security
   controls. Extensions need tests for TUI and noninteractive modes.

## Work packages (internal order, not partial public releases)

- [x] WP1: structural source-to-target obligation matrix for every skill, role, hook and rule;
      source files and source specs have drift hashes. Individual behavioral
      certification is intentionally separate and not checked off by this.
- [ ] WP1b: final human audit of per-workflow requirements in real games;
      record decisions and all transitive references, not only direct flags.
- [ ] WP2: isolated Pi package skeleton, asset and game-root resolution, config
      reader and fixture tests covering precedence, malformed YAML and missing
      tools. No automatic edits of an existing game on package installation.
- [ ] WP3: onboarding/design workflows and relevant role contracts.
- [ ] WP4: architecture, planning, implementation and review workflows.
- [ ] WP5: QA, specialist, team, production and release workflows.
- [ ] WP6: hook/rule replacements, documentation, lifecycle and failure tests.
- [ ] WP7: verify complete cross-workflow lifecycle, engine-specific paths,
      package installation/update/removal, and model switching; release only
      when every contract is satisfied.

## Release gate

- 74/74 Pi skills individually load and pass contract checks; all 49 roles
  have a tested invocation/participation path; all hooks and rules have a
  recorded disposition and tested replacement where required.
- No runnable Pi instruction assumes Claude-only tools, preprocessing, model
  names, or the original template as the writable game root. No dead slash
  commands or missing bundled references.
- Full fresh-game and brownfield lifecycle tests reach release; Godot, Unity,
  and Unreal paths are exercised. Negative tests cover missing input,
  rejected approvals, failed gates and resumption.
- Repeat critical paths on at least two available Pi models from different
  providers; switch models mid-project. Quality may vary, but the same
  artifacts and gates must remain usable.
- Claude Code checks still pass. Installation, update and removal do not
  overwrite game files. Document limitations that cannot be made equivalent.

Until then the Claude Code template remains the supported production route;
no partial Pi package is published or installed globally.
