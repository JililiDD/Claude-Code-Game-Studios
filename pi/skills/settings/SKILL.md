---
name: settings
description: Inspect or change a game's effective project.yaml or local overrides using the bundled CCGS schema. Warn on inactive reserved keys, invalid values and shadowed settings.
---

# Game settings — Pi migration candidate (not released)

Read the full bundled `.claude/skills/settings/SKILL.md` for its view-all,
view-one, team-write, local-write and usage/report contracts. The original
expects `.claude/hooks/yaml-helper.sh` **inside the game**, which a Pi game
does not have. Replace every such call with the tested read-only CLI below;
never edit the framework's `project.yaml` or `.claude` assets. Work in a
separate game directory and use Pi's selected model.

## Parse and inspect

No argument → view all; `<key>` → view one; `<key>=<value>` → write team config;
`--local <key>=<value>` → write personal override. Empty key/value, extra
operands or unsupported syntax show the source Phase 6 usage and write nothing.
Resolve `<framework-root>` from this skill's `../../..` and invoke:

```text
python3 <framework-root>/pi/runtime/settings.py --project <game-root> --action all
python3 <framework-root>/pi/runtime/settings.py --project <game-root> --action show --key <dotted-key>
python3 <framework-root>/pi/runtime/settings.py --project <game-root> --action validate --key <dotted-key> --value <value> [--local]
```

Quote arguments as shell values, never interpolate a user value into shell
code. This CLI validates game YAML strictly, derives reserved settings from
`effects-map.md`, uses the shared schema for enum and whitelist checks,
resolves local → team → rigor → default with provenance, and never writes.
A missing base config, malformed/duplicate YAML, invalid pending enum or locked
local key is a stop condition; no inferred success and no shadowed write
without a warning. For view-all, show `schema_errors` tagged with their file
before rendering grouped `entries`; invalid *existing* enums must be visible,
not called a clean configuration. Show the source's locked and reserved legends. A reserved key can be stored but **does
nothing** today; say that before any approval prompt, including local writes.

## Change only after approval

For a proposed set, show the destination, existing and proposed values,
provenance, local-shadow warning and the actual YAML diff. In collaborative
mode ask "May I write this to [path]?" and wait. Follow the source
`.claude/docs/automation-modes.md` for guided/autonomous choices, but a
team-wide `project.yaml` schema change remains an always-ask category when
configured; a dismissed question is rejection. `studio-approval.ts` adds
file-level confirmation; it does not replace showing the full draft or
multi-file approval. If the user refuses, neither YAML file changes.

Apply a minimal Pi edit to the **game's** `project.yaml` or
`project.local.yaml`, preserving comments, unknown keys and the existing
shape; do not create a second parent block or write a local file without a
base. For ambiguous layout or a merge conflict, stop and ask rather than
rewrite the whole file with a YAML serializer. Re-run `--action show` for the
changed key and, when changing `modes.rigor`, re-read all six fronted knobs
and report their *effective* values, not guessed table values. Keep personal
local overrides outside version control. Never commit or push unrequested.

A single-game config edit is not verification of the full package. The Pi
adapter remains unreleased until user lifecycle validation is complete.
