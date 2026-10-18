#!/usr/bin/env python3
"""Generate unreleased Pi skill candidates pointing to original CCGS contracts.

This is a translation scaffold, NOT a verified port. Hand-adapted skills are
excluded. Re-running updates only generated files; --check validates drift.
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANUAL = {"start", "help", "project-stage-detect", "setup-engine", "skill-test", "skill-improve", "onboard", "settings"}
SOURCE = ROOT / ".claude/skills"
TARGET = ROOT / "pi/skills"


def check_preprocessing(name: str, text: str) -> None:
    """Require every Claude bootstrap expression to have an explicit Pi path."""
    accepted = (
        'bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys ',
        'bash "${CLAUDE_SKILL_DIR}/../../scripts/story-status.sh"',
        'git log ', 'git tag ', 'ls production/sprints/',
    )
    for command in re.findall(r"(?m)^!`([^`\n]+)`", text):
        if not any(command.startswith(prefix) for prefix in accepted):
            raise ValueError(f"Unmapped Claude preprocessing in {name}: {command}")


def render(name: str, text: str) -> str:
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError(f"Missing frontmatter for {name}")
    check_preprocessing(name, text)
    front = text.split("\n---\n", 1)[0]
    names = re.findall(r"(?m)^name:\s*(.*)$", front)
    descriptions = re.findall(r"(?m)^description:\s*(.*)$", front)
    if names != [name] or len(descriptions) != 1:
        raise ValueError(f"Invalid name/description for {name}")
    visibility = "disable-model-invocation: true\n" if re.search(r"(?m)^disable-model-invocation:\s*true$", front) else ""
    refdir = SOURCE / name / "references"
    ref_paths = sorted(refdir.rglob("*.md")) if refdir.is_dir() else []
    combined = "\n".join([text, *(file.read_text(encoding="utf-8") for file in ref_paths)])
    check_preprocessing(name, combined)
    known = {path.parent.name for path in SOURCE.glob("*/SKILL.md")}
    linked = sorted(other for other in known if other != name and
                    re.search(rf"(?<![\w/])/{re.escape(other)}\b", combined))
    prelude = re.findall(r"(?m)^!`([^`\n]+)`", combined)
    gate_names = {path.stem.upper() for path in (ROOT / ".claude/docs/director-gates").glob("*.md")}
    gates = sorted(set(re.findall(r"\b[A-Z]{2}-[A-Z][A-Z0-9-]+\b", combined)) & gate_names)
    def bullets(items):
        return "\n".join(f"- `{item}`" for item in items) if items else "- None found in the bundled source; inspect prose before calling a different workflow."
    reference_list = bullets([file.relative_to(SOURCE / name).as_posix() for file in ref_paths])
    workflow_list = bullets([f"/skill:{other}" for other in linked])
    prelude_list = bullets(prelude)
    gate_list = bullets([f"{gate} → ccgs_gate_review {gate.lower()}" for gate in gates])
    import yaml
    catalog = yaml.safe_load((ROOT / "CCGS Skill Testing Framework/catalog.yaml").read_text(encoding="utf-8"))
    spec = next((row.get("spec") for row in catalog["skills"] if row["name"] == name), None)
    spec_note = (f"Read the bundled `{spec}` for this workflow's named scenarios and failure expectations; "
                 "the spec is an obligation, not a passed test." if spec and (ROOT / spec).is_file()
                 else "No dedicated source test spec exists; inspect all phases and required failure paths directly.")
    special = {
        "perf-profile": """- Phase 2's four `get_effective_yaml_key` calls do NOT run from the
  game with `source .claude/hooks/yaml-helper.sh`. Read each explicitly using
  `python3 <framework-root>/pi/runtime/settings.py --project <game-root>
  --action show --key performance.target_framerate` and repeat for
  `performance.frame_budget_ms`, `performance.draw_call_limit` and
  `performance.memory_ceiling_mb`. Use `value` and `source` in the JSON,
  respecting local overrides. Missing budget and missing measured profiler
  output remain NOT ASSESSED; never treat a design template placeholder as
  a measured budget.
""",
        "design-review": """- Use `python3 <framework-root>/pi/runtime/scripts.py --project
  <game-root> --name review-receipts check <game-relative-receipt>
  <game-relative-document>` for Phase 1 and `--name review-receipts hash
  <game-relative-document>` for the final stamp. The source's literal
  `bash .claude/scripts/review-receipts.sh` has no game-local path in Pi.
  Run `--name gdd-structure-check <game-relative-document>` for the
  structure check. An unresolved receipt glob cannot authorize skipping
  a review; CHANGED/NEW requires re-review.
""",
    }.get(name, "- No additional source-only shell calls were identified; follow the full bundled workflow.\n")
    return f"""---
name: {name}
description: {descriptions[0]}
{visibility}---

# {name} — Pi migration candidate (NOT verified or released)

The original detailed workflow is bundled at
`<framework-root>/.claude/skills/{name}/SKILL.md`. Resolve `<framework-root>`
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

## Source-specific handoff inventory for `{name}`

{spec_note}

Read the following bundled reference files when the source phase calls for
one; their paths are relative to the **source skill directory**, never the
game. These are search leads, not permission to skip any other cited file:
{reference_list}

The source mentions these other workflow commands. The Pi invocation form
is listed, but its approval, failure and dependency rules must be checked
before chaining:
{workflow_list}

Preprocessed source commands that **must be run explicitly** if their phase
is reached (and against the game root):
{prelude_list}

Named independent director gates in the source or its references, if their
conditions are reached. Each uses complete game evidence and is NOT ASSESSED
until the separate Pi tool result is inspected:
{gate_list}

Additional source-specific Pi translation:
{special}
This candidate intentionally stays out of the package manifest until its
individual behavior and dependencies have been tested. It does not certify
that `{name}` works end-to-end in Pi.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--register", action="store_true", help="mark generated candidates draft, never verified")
    args = parser.parse_args()
    if args.check and args.register:
        parser.error("--check and --register are exclusive")
    registry_path = ROOT / "pi/migration/contracts.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if args.register else None
    errors = []
    for source in sorted(SOURCE.glob("*/SKILL.md")):
        name = source.parent.name
        if name in MANUAL:
            continue
        target = TARGET / name / "SKILL.md"
        expected = render(name, source.read_text(encoding="utf-8"))
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != expected:
                errors.append(str(target.relative_to(ROOT)))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected, encoding="utf-8")
            source_key = source.relative_to(ROOT).as_posix()
            if registry is not None and registry["skills"][source_key]["state"] == "pending":
                registry["skills"][source_key] = {
                    "state": "draft", "target": target.relative_to(ROOT).as_posix(),
                    "note": "Generated compatibility candidate; behavior NOT verified",
                }
    if registry is not None:
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        parser.exit(1, "Candidate drift: " + ", ".join(errors) + "\n")
    print("Candidate wrappers current; none has been verified by generation")


if __name__ == "__main__":
    main()
