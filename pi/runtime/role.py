#!/usr/bin/env python3
"""Read a CCGS role as instructions for Pi's CURRENT model (not an agent)."""

import argparse
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
ROLES = PACKAGE_ROOT / ".claude/agents"


def names():
    return sorted(path.stem for path in ROLES.glob("*.md") if path.is_file())


def load(name: str) -> str:
    # Do not allow a caller to read arbitrary files by passing an agent name.
    if name not in names():
        raise ValueError(f"Unknown CCGS role: {name}. Choose from --list")
    text = (ROLES / f"{name}.md").read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError(f"Role {name} has no valid frontmatter")
    return text.split("\n---\n", 1)[1].strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--list", action="store_true")
    options.add_argument("--name")
    args = parser.parse_args()
    if args.list:
        print("\n".join(names()))
        return
    try:
        print(load(args.name))
    except ValueError as exc:
        parser.exit(1, f"Pi CCGS role: {exc}\n")


if __name__ == "__main__":
    main()
