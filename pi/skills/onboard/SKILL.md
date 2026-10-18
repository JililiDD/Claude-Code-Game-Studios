---
name: onboard
description: Orient a new game contributor or specialist using the actual game project, Pi framework role definition and current production state. Missing inputs are explicitly not assessed.
---

# Contributor onboarding — Pi migration candidate (not released)

Use the bundled `.claude/skills/onboard/SKILL.md` for the report schema and
its missing-data discipline, with the following **Pi-specific authority**.
The package remains unreleased; this candidate is not production-verified.

## Phase 1 — Establish game and framework roots

The current working directory is the writable game root; the framework is
three parents above this skill directory. Stop if the game overlaps the
framework. Do **not** require or create `CLAUDE.md` or `.claude/agents/` in
the game: the framework ships the role files and Pi injects project guidelines
through `pi/extensions/studio-guidelines.ts`. Check that the framework's
`.claude/agents/` exists; absent package assets mean NOT ASSESSED, not an
instruction to copy the entire framework into the game.

Read game `project.yaml` and optional `docs/technical-preferences.md`, game
brief/GDDs, and game-owned engine reference. Obtain effective `automation` and
`engine` using `python3 <framework-root>/pi/runtime/config.py --project
<game-root> --keys automation,engine`. Stop rather than using framework
`project.yaml` when the game's config is missing. Ask for the role/area if
necessary. For a named specialist read the exact bundled
`.claude/agents/<role>.md` and optional corresponding Pi role skill. A missing
role is NOT ASSESSED; do not pretend the role was consulted independently.

## Phase 2 — Scan with explicit missing-data accounting

Follow the source Phase 2 area routing. Resolve code root using bundled
`.claude/docs/code-root-resolution.md`, scoped to the game; do not guess
`src/`. Scan game design, architecture, tests, production/sprints, and
`production/session-state/active.md` only where relevant. Read recent game
Git history if present. For every required input write FOUND or ABSENT. Any
section depending on absent data reads `NOT ASSESSED — NO DATA`; if all required
inputs are absent, stop with that overall verdict and list their producer
workflows. Do not fill gaps from the framework's example project.

## Phase 3 — Draft and approve

Use the original Phase 3 onboarding schema, but cite **game** paths for
standards, state, code and priorities; cite framework role definitions
separately. A Pi single-session role summary is not an independent specialist
review. Recommend first tasks conditioned on actual available data. Show the
complete draft and ask "May I write this to
`production/onboarding/onboard-<role>-<date>.md`?" Wait for an explicit
answer before creating the game file. Never write the framework or commit.

Report COMPLETE only if the report's required data was assessed and the output
actually exists; otherwise state precisely what remains NOT ASSESSED. Suggest
`/skill:sprint-status` and `/skill:help` as contextual next steps.
