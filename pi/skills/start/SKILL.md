---
name: start
description: Set up a new or existing game project for the CCGS workflow in Pi. Use when explicitly onboarding a game, not for the framework checkout itself.
---

# Start — Pi migration candidate (not released)

This skill is a **port of the onboarding entry point**, not a copy of Claude's
`/start`. The full adapter is unreleased; use it only in a disposable game
fixture until every dependent skill has passed the release gate. Do not claim
that later commands are available in Pi yet.

## Boundaries

- The directory holding this `SKILL.md` is inside the installed framework.
  Resolve its grandparent's parent to find the framework root and bundled
  `project.yaml`, `.claude/docs/` and `pi/runtime/config.py` references.
- The current working directory is the **game root**. Never edit the framework
  checkout. If the game root equals or is inside the framework checkout, stop.
  If the game root is not explicit or cannot be distinguished, ask first.
- Use Pi's current model. There is no role or model switch in this skill.
  Ask questions in normal conversation; never invoke `AskUserQuestion` or
  pretend that a separate agent reviewed your choices.
- Do not create a git repository, change git remotes, install extensions or
  overwrite existing project configuration as a side effect of onboarding.

## 1. Examine the game before asking

Read `project.yaml` if present, otherwise check for existing game source,
`design/game-brief.md`, `design/gdd/`, `production/` and engine markers. Read
`project.local.yaml` if present. A configured engine plus a concept/brief means
this may be a returning user: give a concise status and ask whether they want
onboarding or guidance. Do not overwrite their settings.

If `project.yaml` exists, resolve effective modes with the bundled helper:
`python3 <framework-root>/pi/runtime/config.py --project <game-root> --keys automation,workflow,review_mode,qa.level`.
Only substitute verified absolute paths; quote shell arguments. If resolution
fails, show the error and stop rather than silently using defaults. On a fresh
game without a config, the rigor default is `minimal` and automation default
is `collaborative`.

## 2. Establish the starting point

Ask which describes their game: (A) no idea, (B) vague idea, (C) clear
concept, (D) existing work. Wait for the answer. For C ask for the concept in
one sentence; for D report the files found and ask which existing materials
should be preserved. Recommend the immediate next action without starting it:
exploration/design for A–C, project assessment/adoption for D. Do not claim
that an unported Pi workflow is already available.

## 3. Choose and confirm settings

Show the user the proposed initial stage and why: new idea or only concept →
`Concept`; existing GDDs but no architecture → `Systems Design`; existing
architecture → `Technical Setup`. Ask for permission to create/update
`project.yaml` and its legacy stage mirror `production/stage.txt`, naming both
files. A rejection means neither file is changed.

Then ask for rigor: `minimal` (short brief and coarse stories), `standard`
(balanced documentation and QA), or `full` (thorough documentation and
reviews). Recommend `minimal` for an undecided small prototype; give reasons
for a higher recommendation when complexity warrants it. Ask for automation:
`collaborative` (confirm significant writes), `guided` (confirm major calls),
or `autonomous` (still confirm scope changes, deletions and schema changes).
These are project decisions; wait for the user's choices. When the user has
already configured a value, report it rather than asking to replace it.

## 4. Write only the approved game files

For a **fresh game**, once the user has approved both files and selected all
three values, invoke the bundled CLI with verified, quoted absolute paths:

```text
python3 <framework-root>/pi/runtime/init_game.py --project <game-root> --stage <approved-stage> --rigor <approved-rigor> --automation <approved-automation>
```

The CLI uses exclusive creation and refuses to overwrite either destination.
Do not call it for a partly configured or existing project. Do not add any of
the six keys fronted by `rigor` (`modes.workflow`, `modes.review_mode`,
`modes.story_granularity`, `docs.density`, `qa.level`, `team.size`): explicitly
adding one would shadow the user's rigor choice. For an existing config, edit
only the approved keys while retaining unknown fields, comments and existing
structure. Do not write a second `modes:` block or overwrite local overrides.
If approval covered stage but the user declined the later settings, only stage
may be saved; do not invent their choice or call the fresh-game CLI.

Never commit or push. Re-run the bundled config resolver for the game root and check
its resolved values and provenance against the user's choices. Check that the
framework checkout remains unchanged. Report files changed and unresolved
questions. Until the full Pi port is released, explain that next-stage Pi
workflows are not yet production-ready; the Claude Code template remains the
supported production route.
