#!/usr/bin/env python3
"""Generate per-role Pi skill candidates from the 49 Claude role contracts.

These skills use Pi's current model in the current session. Generating one is
not evidence that its behavior, tool grants or escalation path is equivalent.
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / ".claude/agents"
TARGET = ROOT / "pi/skills"


def render(role: str, source: str) -> str:
    if not source.startswith("---\n") or "\n---\n" not in source[4:]:
        raise ValueError(f"Missing role frontmatter: {role}")
    front = source.split("\n---\n", 1)[0]
    names = re.findall(r"(?m)^name:\s*(.*)$", front)
    descriptions = re.findall(r"(?m)^description:\s*(.*)$", front)
    if names != [role] or len(descriptions) != 1:
        raise ValueError(f"Missing role name/description: {role}")
    import yaml
    catalog = yaml.safe_load((ROOT / "CCGS Skill Testing Framework/catalog.yaml").read_text(encoding="utf-8"))
    spec = next((entry.get("spec") for entry in catalog["agents"] if entry["name"] == role), None)
    if not spec or not (ROOT / spec).is_file():
        raise ValueError(f"Missing source role test spec for {role}")
    return f"""---
name: ccgs-{role}
description: {descriptions[0]}
---

# {role} — Pi role migration candidate (NOT verified or released)

This skill applies the CCGS `{role}` domain guidance with **Pi's currently
selected model**, not the hardcoded model in the Claude Code role. Resolve the
framework root from this skill directory via `../../..` and first read
`<framework-root>/pi/skills/ccgs-role/SKILL.md`. Then read
`<framework-root>/.claude/agents/{role}.md` **in full** and read its
`<framework-root>/{spec}` scenario expectations before declaring it complete.
The source test spec is an obligation, NOT proof of a passing Pi test. Apply
its body under the Pi-specific rules in `ccgs-role`. Resolve all `.claude/` references
against the framework; game artifacts live in the current game root.

Label the result as a **single-session role pass**. For a fresh, independently
drafted role contribution use `ccgs_role_consult` with a brief and evidence;
its output is unsaved and the main session writes only after approval. For an
independent named director gate use `ccgs_gate_review`; if unavailable or
NOT ASSESSED, leave the gate open. Do not launch a subagent just because the
original role mentions one. Ask before writes as
required by the game's automation mode. This is a draft until its individual
role and workflow integrations have been verified.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--register", action="store_true")
    args = parser.parse_args()
    if args.check and args.register:
        parser.error("--check and --register are exclusive")
    registry_path = ROOT / "pi/migration/contracts.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if args.register else None
    stale = []
    for source in sorted(SOURCE.glob("*.md")):
        role = source.stem
        target = TARGET / f"ccgs-{role}" / "SKILL.md"
        expected = render(role, source.read_text(encoding="utf-8"))
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != expected:
                stale.append(target.relative_to(ROOT).as_posix())
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected, encoding="utf-8")
            key = source.relative_to(ROOT).as_posix()
            if registry is not None and registry["agents"][key]["state"] == "pending":
                registry["agents"][key] = {
                    "state": "draft", "target": target.relative_to(ROOT).as_posix(),
                    "note": "Generated single-session role candidate; behavior NOT verified",
                }
    if registry is not None:
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if stale:
        parser.exit(1, "Stale role candidates: " + ", ".join(stale) + "\n")
    print("49 role candidates generated/checked; this is not behavioral verification")


if __name__ == "__main__":
    main()
