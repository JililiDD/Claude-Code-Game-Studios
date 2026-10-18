---
name: setup-engine
description: Configure a Godot, Unity or Unreal game engine and version in a separate CCGS game project; verify engine installation, game-owned references and runnable scaffold. Use for guided setup, refresh, or upgrade.
---

# Engine setup for Pi — migration candidate (not released)

This is the Pi adaptation of the bundled `.claude/skills/setup-engine/` domain
workflow. Read that source's referenced sections **only as domain guidance**;
the path and tool substitutions below override conflicting Claude Code steps.
Do not run this against the framework checkout. The Pi package is currently
unreleased; exercise this candidate only in a disposable game fixture.

## Roots and authority

- `<framework-root>` is three parents above this skill directory; it contains
  read-only `.claude/skills/setup-engine/references/` and
  `docs/engine-reference/{godot,unity,unreal}/`. `<game-root>` is the current
  working directory, independent of that framework. If they overlap, stop.
- `project.yaml`, `docs/technical-preferences.md`,
  `docs/engine-reference/<engine>/`, and engine source are **game-owned**.
  Never update the framework's `CLAUDE.md`, `.claude/agents/`,
  `.claude/docs/technical-preferences.md`, or bundled reference documents.
  Unlike Claude Code, Pi has no CLAUDE.md engine import to update: resolve
  the engine from the game's `project.yaml`, then read that game's pinned
  `docs/engine-reference/<engine>/VERSION.md` on demand. An absent game-owned
  file is a gap, not permission to modify the package.
- Pi's currently selected model is used throughout. Ask decisions in normal
  conversation, wait for answers, and never claim a role or tool was run if it
  was not. Source `AskUserQuestion`, `Agent`, `WebSearch` and `!` lines are
  Claude-specific: use Pi's available conversational, research and shell
  tools. If current version cannot be independently confirmed, ask the user
  to supply an exact version or stop that branch; never guess.

## Select, verify, and approve

1. Resolve the game's `workflow` and `engine` independently with
   `python3 <framework-root>/pi/runtime/config.py --project <game-root> --keys workflow,engine`.
   If game config does not exist, first use `/skill:start`; never use the
   framework's `project.yaml` as a substitute. Read the current game files
   before proposing replacements.
2. Parse arguments as **engine + version**, **engine only**, **guided (none)**,
   **refresh**, or **upgrade old new**. For guided choice and language routing,
   read the source `references/2-guided-mode.md` and, for Godot only,
   `references/godot-language-config.md`. Resolve language, rendering, physics,
   target platforms and actual binary paths with the user. Determine engine
   version with verified current release information (source
   `references/3-version.md`); distinguish a downloaded editor, a verified
   upstream release, and an unverified requested version.
3. Present a change plan naming every game file to create or edit, the exact
   version and its source, expected engine binary, and any settings that remain
   uncertain. Ask for approval of the full set before writing. If the user
   rejects a write, leave related config/reference/scaffold unchanged; do not
   leave conflicting versions. Refuse accidental overwrites and preserve
   unknown YAML keys, comments and local overrides.

## Configure the game, not the package

4. Use source `references/5-technical-preferences.md` for domain choices and
   `references/5.5-project-yaml.md` for the schema and engine-specific command
   design. Write approved `engine`, `specialists`, `naming`, and `commands`
   blocks to the **game's** `project.yaml`. If a legacy mirror is useful,
   write approved preferences under the **game's**
   `docs/technical-preferences.md`, clearly marked as subordinate to
   `project.yaml`. Do not edit the framework fallback document. For Godot,
   distinguish GDScript, C#, or Both; GDExtension alone does not make C++ the
   primary language. Check commands against actual editor path and platform;
   never substitute a guessed executable or launch argument.
5. For version/reference knowledge, read source `references/6-knowledge-gap.md`
   and `references/7-reference-docs.md`. The bundled engine reference is an
   example, not necessarily the user's installed version. Copy **only after
   approval** the applicable reference files into the game's
   `docs/engine-reference/<engine>/`, then adapt and cite the verified exact
   version. Do not silently publish unverified APIs or overwrite a different
   engine's material. Record an `Installed at pin time` row in `VERSION.md`
   with the actual probe result or explicitly `NOT DETERMINED`.
6. Read source `references/7.5-scaffold.md` for the chosen engine. Create the
   approved minimal game scaffold if needed. For Godot parse checks, the
   original `res://.claude/scripts/` path does not exist in a Pi-only game:
   with explicit approval run `python3 <framework-root>/pi/runtime/godot_check.py
   --project <game-root> --stage --approved`, then use `--command` with each
   changed script to obtain the game-owned checker path. Staging never runs
   an engine. If engine binaries exist, run the source-documented native
   validation and retain the result. If absent, say
   engine execution is **NOT VERIFIED**, not merely that parsing passed.
   Never count a simulated runner as a real engine run. For player-visible
   changes later, `.claude/docs/run-and-observe.md` still requires actual
   observation and retained screenshot evidence.

## Refresh, upgrade, and final verification

- **Refresh** updates only the game's reference files after current release
  research and approval; it does not change `engine.version` unless the user
  explicitly chooses an upgrade. **Upgrade** follows domain checks in source
  `references/11-upgrade.md`, probes affected code and migration APIs, then
  seeks approval for coordinated config, reference and source changes. Both
  preserve the prior version until the new one is verified. Do not edit shared
  role files; fresh `ccgs_role_consult` requests receive the game's pinned
  reference as evidence when specialist input is required.
- Re-read the game's `project.yaml`, pinned VERSION, preferences and project
  file. Resolve `engine` again using the CLI. Run
  `python3 <framework-root>/pi/runtime/scripts.py --project <game-root> --name project-coherence`
  and interpret each `[DIFFERS]` and `[NOT CHECKED]` line; the script emits
  observations, not a pass/fail verdict. If the binary/scaffold could not be
  executed, keep that gate open. Use source `references/12-output-summary.md`
  for the final report, but replace CLAUDE.md updates with the game-owned
  config/reference evidence above. State precisely what was written, what was
  run, and what remains blocked. Do not commit or push without user request.
