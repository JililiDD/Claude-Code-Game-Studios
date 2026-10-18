---
name: help
description: Orient a CCGS game project in Pi and identify its next step from resolved settings, the workflow catalog and on-disk evidence. Use when the developer asks what to do next.
---

# Studio help — Pi migration candidate (not released)

Read-only. The current working directory must be an **independent game root**,
not the framework checkout. Resolve the framework root from this skill file's
`../../..` ancestor. Never edit a game file while answering `/skill:help`.
Do not assume Claude Code preprocessing, skill locations or available agents.

## Evidence collection

1. Run `python3 <framework-root>/pi/runtime/config.py --project <game-root>
   --keys project.stage,workflow`, with quoted absolute paths. If no game
   `project.yaml` exists, suggest `/skill:start` and stop. Do not infer a
   default tier when resolution failed.
2. Read `<framework-root>/.claude/docs/workflow-catalog.yaml` for the ordered
   phases and the `paths.minimal` route. This is a **framework asset**, not a
   game file.
3. Read `production/session-state/active.md` in the game if present, focusing
   on its STATUS and CHECKPOINT sections. Respect the user's description of
   what they have just completed; a file's presence is not proof of a gate's
   verdict.
4. For `workflow: minimal`, run
   `python3 <framework-root>/pi/runtime/artifacts.py --project <game-root>
   --path minimal` and `python3 <framework-root>/pi/runtime/stories.py
   --project <game-root>`. For other tiers, map the resolved `project.stage`
   to the matching catalog phase and run the artifacts command with
   `--phase <phase-id>`. In production, read the game's
   `production/sprint-status.yaml` if present; its per-story states take
   precedence over glob-based story counts.
5. If any checker fails, report its error. Never claim a phase complete based
   on missing data. Checker results are observations: `NO_CHECK` means
   **unknown/manual**, `ABSENT`, `SHORT` and `PATTERN_MISS` mean incomplete;
   `PRESENT` means the artifact check succeeded, not that human review passed.

## Routing

- At `minimal`, follow the catalog's `paths.minimal` only; do not demand a
  GDD, art bible, sprint or phase gate. First incomplete prerequisite wins:
  engine setup → brief → stories. Once stories exist, their ordered status
  determines the next step: first `IN_REVIEW` → story closure; first
  `IN_PROGRESS` → continue implementation unless the user confirms it is
  written and awaits closure; first `TODO` → implementation. Never treat a
  blocked or unknown-status story as completed. When all are complete, offer
  a playtest, more stories or raising rigor.
- At `standard`/`full`, follow the current catalog phase in order. Distinguish
  required from optional steps, and repeatable from finished work. Show the
  first incomplete required step and any relevant blocker. A verdict must
  come from the corresponding actual review, not the mere existence of files.
- In every tier, surface an active checkpoint before proposing new work.
  Return a short summary: current stage, known completed work, first next
  action, blockers and why. If an artifact is ambiguous, say so explicitly.

This migration candidate is not a released Pi workflow suite. **Never tell a
user an unported command is available in Pi.** When the next skill remains
unverified in `pi/migration/contracts.json`, describe that workflow step as
pending Pi migration and say Claude Code is the supported route for production
until the full port passes its release gate. Do not offer `team-*` or other
Claude-only commands as working Pi actions.
