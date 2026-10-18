#!/usr/bin/env python3
"""Inventory Claude Code dependencies before migrating resources to Pi.

This is a source inventory, not proof that a converted workflow behaves correctly.
Run from anywhere: python3 pi/migration/audit.py [--check]
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".claude" / "skills"
AGENTS = ROOT / ".claude" / "agents"

# These are behavioral dependencies, not merely frontmatter differences.
PATTERNS = {
    "shell_preprocessing": r"!`",
    "claude_skill_dir": r"\$\{CLAUDE_SKILL_DIR\}",
    "claude_project_dir": r"\$\{CLAUDE_PROJECT_DIR\}",
    "ask_user_question": r"\bAskUserQuestion\b",
    "agent_dispatch": r"\bAgent(?:\s*\(|\s+tool\b|\s+in\s+parallel\b|\s+calls?\b|\s+to\b|\s+for\b)",
    "claude_tree_reference": r"\.claude/",
    "claude_tool_grant": r"\b(?:allowed-tools|tools):",
    "model_pin": r"(?m)^model:\s*(?!inherit\s*$)\S+",
}


def inventory_file(path, root=ROOT):
    text = path.read_text(encoding="utf-8")
    flags = sorted(key for key, pattern in PATTERNS.items() if re.search(pattern, text))
    referenced = sorted(set(re.findall(r"(?<![\w/])/(?:[a-z][a-z0-9-]+)\b", text)))
    return {
        "name": path.parent.name if path.name == "SKILL.md" else path.stem,
        "source": path.relative_to(root).as_posix(),
        "flags": flags,
        "slash_references": referenced,
    }


def inventory(root=ROOT):
    skills = [inventory_file(path, root) for path in sorted((root / ".claude/skills").glob("*/SKILL.md"))]
    known = {item["name"] for item in skills}
    for item in skills:
        item["known_skill_references"] = sorted({ref[1:] for ref in item["slash_references"]
                                              if ref[1:] in known and ref[1:] != item["name"]})
    agents = [inventory_file(path, root) for path in sorted((root / ".claude/agents").glob("*.md"))]
    hooks = sorted(path.relative_to(root).as_posix() for path in (root / ".claude/hooks").glob("*.sh"))
    rules = sorted(path.relative_to(root).as_posix() for path in (root / ".claude/rules").glob("*.md"))
    return {
        "schema_version": 1,
        "note": "Source inventory only; every resource remains unverified for Pi until tested.",
        "counts": {"skills": len(skills), "agents": len(agents), "hooks": len(hooks), "rules": len(rules)},
        "skills": skills,
        "agents": agents,
        "hooks": hooks,
        "rules": rules,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the tracked source inventory is stale")
    args = parser.parse_args()
    target = ROOT / "pi/migration/inventory.json"
    expected = json.dumps(inventory(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != expected:
            parser.exit(1, f"Outdated {target.relative_to(ROOT)}; rerun python3 pi/migration/audit.py\n")
        print(f"Inventory current: {target.relative_to(ROOT)}")
    else:
        target.write_text(expected, encoding="utf-8")
        print(f"Wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
