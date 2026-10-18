#!/usr/bin/env python3
"""Verify every source resource has one tracked Pi migration disposition.

To bootstrap a *new* registry: python3 pi/migration/contracts.py --init
Afterwards edit contract states by hand; --init refuses to replace it.
"""

import argparse
import json
from pathlib import Path

from audit import ROOT, inventory

REGISTRY = ROOT / "pi/migration/contracts.json"
RESOURCE_TYPES = ("skills", "agents", "hooks", "rules")
STATES = {"pending", "draft", "verified", "inapplicable"}


def initial_registry():
    data = inventory()
    registry = {}
    for kind in RESOURCE_TYPES:
        registry[kind] = {}
        for entry in data[kind]:
            source = entry["source"] if isinstance(entry, dict) else entry
            registry[kind][source] = {
                "state": "draft" if source == ".claude/skills/start/SKILL.md" else "pending",
                "target": "pi/skills/start/SKILL.md" if source == ".claude/skills/start/SKILL.md" else None,
                "note": "Pi onboarding candidate; not released" if source == ".claude/skills/start/SKILL.md" else "",
            }
    return registry


def check_registry(registry):
    expected = initial_registry()
    errors = []
    for kind in RESOURCE_TYPES:
        actual = registry.get(kind, {})
        missing = sorted(set(expected[kind]) - set(actual))
        extra = sorted(set(actual) - set(expected[kind]))
        if missing or extra:
            errors.append(f"{kind}: missing={missing}, extra={extra}")
        for source, contract in actual.items():
            state = contract.get("state")
            if state not in STATES:
                errors.append(f"{source}: invalid state {state}")
            target = contract.get("target")
            if state in {"draft", "verified"} and (not target or not (ROOT / target).is_file()):
                errors.append(f"{source}: {state} needs an existing target")
            if state == "inapplicable" and not contract.get("note"):
                errors.append(f"{source}: inapplicable needs an explanation")
            if state == "verified":
                evidence = contract.get("evidence", [])
                if not evidence or any(not (ROOT / item).is_file() for item in evidence):
                    errors.append(f"{source}: verified needs existing evidence paths")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init", action="store_true", help="create registry only if absent")
    parser.add_argument("--release", action="store_true", help="require complete verified resource coverage")
    args = parser.parse_args()
    if args.init:
        with REGISTRY.open("x", encoding="utf-8") as file:
            json.dump(initial_registry(), file, ensure_ascii=False, indent=2)
            file.write("\n")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    errors = check_registry(registry)
    if args.release:
        for kind in RESOURCE_TYPES:
            incomplete = [source for source, contract in registry[kind].items()
                          if contract["state"] != "verified" and not
                          (kind in {"hooks", "rules"} and contract["state"] == "inapplicable")]
            if incomplete:
                errors.append(f"{kind}: {len(incomplete)} resources still unverified")
        manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        package = manifest.get("pi", {})
        if "./pi/skills" not in package.get("skills", []):
            errors.append("Pi package does not expose all CCGS skills")
        required_extensions = {f"./pi/extensions/{name}.ts" for name in
                               ("studio-gates", "studio-rules", "studio-checks", "studio-session", "studio-guidelines", "studio-approval")}
        if not required_extensions.issubset(set(package.get("extensions", []))):
            errors.append("Pi package is missing gate, rule or validation extensions")
    if errors:
        parser.exit(1, "\n".join(errors) + "\n")
    print("Registry covers all source resources (NOT a Pi release certification)")
    print("States:", {kind: {state: sum(x["state"] == state for x in registry[kind].values())
                             for state in sorted(STATES)} for kind in RESOURCE_TYPES})


if __name__ == "__main__":
    main()
