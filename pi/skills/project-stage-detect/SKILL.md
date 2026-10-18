---
name: project-stage-detect
description: Inspect a CCGS game project's actual stage, compare it to configuration and report tier-appropriate gaps. Use when adopting existing work or assessing progress.
---

# Project stage detection — Pi migration candidate (not released)

The working directory is the game root, not the framework checkout. Resolve
this skill's `../../..` ancestor as the framework root. Do not run from the
framework checkout. Use Pi's current model and native read/bash tools; no
Claude `!` preprocessing or `AskUserQuestion` exists here.

1. Resolve `workflow,automation,project.stage` with
   `python3 <framework-root>/pi/runtime/config.py --project <game-root>
   --keys workflow,automation,project.stage` (quote the absolute paths). If
   the game lacks `project.yaml`, say onboarding/adoption is needed; continue
   a read-only artifact and source inventory, but leave configured tier,
   automation and engine **NOT ASSESSED**. Do not run the resolver against
   the installed framework to substitute values. If `project.yaml` exists
   but the resolver fails (malformed/duplicate YAML or missing dependency),
   stop config-dependent decisions, report the error, and offer only
   read-only inventory; never substitute guessed defaults.
2. Run `python3 <framework-root>/pi/runtime/artifacts.py --project
   <game-root> --all` once for all catalog phases. Read additional game
   documents only to assess content and gaps that the checker cannot assess.
   The catalog and stage-report template are framework assets at
   `<framework-root>/.claude/docs/workflow-catalog.yaml` and
   `<framework-root>/.claude/docs/templates/project-stage-report.md`.
   Catalog statuses are observations, **not** phase-gate approvals;
   `NO_CHECK` means no conclusion can be drawn from existence alone.
3. Resolve source root with
   `python3 <framework-root>/pi/runtime/code_root.py --project <game-root>`.
   It uses configured Godot `src/`, Unity `Assets/`, Unreal `Source/`, a
   game-owned legacy preference or an unambiguous directory; see bundled
   `.claude/docs/code-root-resolution.md`. If still unresolved, report source
   count and production classification as **NOT ASSESSED**, never zero. Count
   actual source, design, ADR, prototype and test files.
4. Derive observed stage separately from `project.stage`: absent concept →
   Concept; concept without systems index → Systems Design; systems index
   without engine → Technical Setup; configured engine and <10 source files
   → Pre-Production; 10+ source files → Production. Polish and Release need
   explicit gate evidence. Show **both** configured and observed stages. A
   discrepancy means `CONCERNS`, except expected Concept lag at `minimal`
   (phase gates are not used at that tier). Lack of a check needed to decide
   the stage yields `NOT ASSESSED`; a known critical blocker is `FAIL`.
5. Surface gaps by effective tier: `minimal` needs an engine, brief, stories
   and runnable work, not GDDs/ADRs/sprint plans; `standard` requires core
   design and critical ADRs; `full` reports all required artifact gaps. Ask
   whether apparent gaps are recorded elsewhere before recommending creation.
   Do not report arbitrary completion percentages without a stated denominator.
6. Present a concise report with evidence, stage confidence, missing inputs,
   tier-appropriate next steps and any configured/observed discrepancy. If the
   user wants a persisted report, show the draft, ask permission for
   `production/project-stage-report.md`, and write **only** after approval.
   Never commit or push. A role filter (`programmer`, `designer`, `producer`)
   affects emphasis, not the underlying facts.

This candidate does not certify downstream Pi commands as working. Consult
`<framework-root>/pi/migration/contracts.json` before offering a Pi next-step
command; if it remains pending/draft, say it is not yet released.
