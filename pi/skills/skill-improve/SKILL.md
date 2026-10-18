---
name: skill-improve
description: Improve one Pi CCGS skill with a measured baseline, targeted fix and retest. Maintainer-only writes in the framework fork; never edit installed framework resources from a game.
---

# Skill improvement — Pi maintainer candidate (not released)

The original `.claude/skills/skill-improve/SKILL.md` describes a
measure → diagnose → propose → write → retest → keep/revert loop. Preserve that
loop, but target the Pi implementation rather than overwriting the Claude Code
source. The full adapter remains unreleased; its generated wrappers and source
specs are not automatically verified.

## Preconditions

Require an exact skill slug; otherwise show `/skill:skill-improve <skill>` and
stop. Resolve the framework root from this skill directory, identify
`pi/skills/<skill>/SKILL.md`, and read the source skill plus all relevant
`references/` files. Verify whether the framework root is a **writable,
maintainer-controlled Git checkout** on a feature branch and the user has
requested changing that checkout. A running game must stay a separate root;
never attempt to edit an installed/cached package, source `.claude/` skill,
or game project as a side effect. If the checkout condition fails, offer a
read-only diagnosis and patch proposal, then stop before writes. Do not
interpret game `project.yaml` automation as permission to change the package.

## Baseline and diagnosis

1. Run `/skill:skill-test static <skill>` and, if available, the relevant
   Pi-adapted spec/category checks. Record concrete FAIL/WARN/NOT ASSESSED
   findings, the files and assertions behind each, and currently passing
   properties. Run any relevant unit, RPC, engine or full-lifecycle tests
   **before** editing; if they cannot run, state why. A missing file or failed
   tool is not a clean score.
2. Trace each finding to its actual cause: Pi skill instructions, extension,
   game-root wrapper, shared source asset, missing test or an external engine
   dependency. Fix only the owned Pi layer. If a source Claude bug truly needs
   a change, propose it separately with explicit user approval and regression
   evidence; never conflate a Pi adaptation with a source edit.
3. Show a before/after proposal naming each file, approval and gate behavior,
   and any change to shared framework vs game boundaries. Ask for explicit
   approval of the **full file set** before writing. Silence is not consent.

## Retest and decide

4. Capture the exact pre-edit bytes of every approved file, including
   pre-existing uncommitted changes (do not use `git checkout` to revert).
   Apply the smallest targeted edit. Regenerate candidates only if the
   generator itself changed and only in the framework checkout; hand-adapted
   skills must not be overwritten. Do not silently mark a registry entry
   verified or enable the package manifest.
5. Repeat baseline checks and relevant negative/behavioral tests. Compare
   failures + warnings and show separate NOT ASSESSED items. A newly missing
   assertion or a test that could not execute is **not** an improvement. Keep
   a change only if behavior and score improve without regressing a passing
   requirement; otherwise show the comparison and ask whether to restore
   exactly the captured bytes for every changed file. Do not discard user
   edits made before the run.
6. Report checks run, paths changed, unresolved issues and next test or
   skill. Do not commit or push without user request, and never claim the
   complete Pi port from a single skill's score.
