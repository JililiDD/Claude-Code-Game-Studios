#!/usr/bin/env python3
"""Deterministic source-to-Pi obligation matrix. Not behavioral certification.

The matrix is checked into the branch so a changed source contract or a new
resource cannot silently inherit a prior migration disposition. It describes
what must be exercised in Pi; passing this structural check does not mark any
resource verified.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from .audit import ROOT, inventory
except ImportError:  # direct CLI entry point
    from audit import ROOT, inventory

TARGET = ROOT / "pi/migration/behavior-matrix.json"
REGISTRY = ROOT / "pi/migration/contracts.json"
OPTIONAL_OR_GAME_REFERENCES = {
    ".claude/docs/templates/patch-notes-template.md": "Optional source fallback; patch-notes checks for a game template first",
    ".claude/agent-memory/": "Game-local path pattern in the Claude-only agent memory rule; not a bundled file",
}
SOURCE_SKILLS = ROOT / ".claude/skills"
SOURCE_ROLES = ROOT / ".claude/agents"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def references(text):
    paths = re.findall(r"(?<![\w/])\.claude/(?:[a-zA-Z0-9_.-]+/?)+", text)
    # End punctuation is prose; a trailing '-' is usually a wrapped comment.
    return sorted({path.rstrip(".,:;`") for path in paths if not path.endswith("-")})


def build():
    found = inventory()
    contracts = json.loads(REGISTRY.read_text(encoding="utf-8"))
    names = {item["name"] for item in found["skills"]}
    roles = {item["name"] for item in found["agents"]}
    gate_names = {path.stem.upper() for path in (ROOT / ".claude/docs/director-gates").glob("*.md")}
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to generate the source spec matrix") from exc
    catalog = yaml.safe_load((ROOT / "CCGS Skill Testing Framework/catalog.yaml").read_text(encoding="utf-8"))
    specs = {kind: {entry["name"]: entry.get("spec") for entry in catalog[kind]}
             for kind in ("skills", "agents")}
    matrix = {"schema_version": 1, "note": "Structural obligations, NOT a Pi behavioral verification", "resources": {}}
    for kind in ("skills", "agents", "hooks", "rules"):
        matrix["resources"][kind] = {}
        for item in found[kind]:
            source = item["source"] if isinstance(item, dict) else item
            path = ROOT / source
            text = path.read_text(encoding="utf-8")
            contract = contracts[kind][source]
            record = {
                "source_sha256": sha(text),
                "target": contract["target"],
                "referenced_framework_assets": references(text),
            }
            if kind == "skills":
                body = text.split("\n---\n", 1)[1]
                refdir = path.parent / "references"
                reference_files = sorted(refdir.rglob("*.md")) if refdir.exists() else []
                combined = "\n".join([body, *(file.read_text(encoding="utf-8") for file in reference_files)])
                record["referenced_framework_assets"] = references(combined)
                record.update({
                    "source_reference_files": {str(file.relative_to(ROOT)): sha(file.read_text(encoding="utf-8"))
                                               for file in reference_files},
                    "other_workflows": sorted({name for name in names if name != item["name"] and
                                               re.search(rf"(?<![\w/])/{re.escape(name)}\b", combined)}),
                    "preprocessing": re.findall(r"(?m)^!`([^`\n]+)`", combined),
                    "requires_user_decision": "AskUserQuestion" in combined or bool(re.search(r"(?i)\b(?:ask|approval|confirm)\b", combined)),
                    "mentions_role_dispatch": bool(re.search(r"(?i)\b(?:spawn|delegate|subagent|agent tool)\b", combined)),
                    "mentions_gate": bool(re.search(r"(?i)\b(?:gate|verdict|blocking)\b", combined)),
                    "named_director_gates": sorted(set(re.findall(r"\b[A-Z]{2}-[A-Z][A-Z0-9-]+\b", combined)) & gate_names),
                    "mentions_error_path": bool(re.search(r"(?i)\b(?:fail|blocked|missing|not assessed|recovery)\b", combined)),
                    "written_artifact_roots": sorted(set(re.findall(r"(?<![\w/])(?:design|docs|production|tests|src|assets)/[\w/*._-]+", combined))),
                })
                assert item["name"] in names
            elif kind == "agents":
                body = text.split("\n---\n", 1)[1]
                record.update({
                    "domain_sections": re.findall(r"(?m)^#{1,3} (.+)$", body),
                    "source_model_pin": (re.search(r"(?m)^model: (.+)$", text) or [None, None])[1],
                    "other_roles": sorted(role for role in roles if role != item["name"] and re.search(rf"\b{re.escape(role)}\b", body)),
                    "mentions_escalation": bool(re.search(r"(?i)\b(?:escalat|collaborat|delegate)\w*", body)),
                })
            unresolved = [ref for ref in record["referenced_framework_assets"] if not (ROOT / ref).exists()]
            unexpected = set(unresolved) - set(OPTIONAL_OR_GAME_REFERENCES)
            if unexpected:
                raise ValueError(f"{source}: missing bundled assets: {', '.join(sorted(unexpected))}")
            record["optional_or_game_references"] = {ref: OPTIONAL_OR_GAME_REFERENCES[ref] for ref in unresolved}
            if kind in ("skills", "agents"):
                spec = specs[kind].get(item["name"])
                record["source_test_spec"] = spec if spec and (ROOT / spec).is_file() else None
                record["source_test_spec_sha256"] = sha((ROOT / spec).read_text(encoding="utf-8")) if record["source_test_spec"] else None
            elif kind == "rules":
                front = text.split("\n---\n", 1)[0]
                record["path_patterns"] = re.findall(r'^\s*-\s*"([^"]+)"\s*$', front, re.M)
            else:
                record["hook_event"] = path.stem
            matrix["resources"][kind][source] = record
    return matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != expected:
            parser.exit(1, "Behavior matrix is stale; rerun python3 pi/migration/behavior_matrix.py\n")
        print("Behavior matrix covers source inputs (NOT behavioral certification)")
    else:
        TARGET.write_text(expected, encoding="utf-8")
        print("Recorded per-resource obligations (NOT behavioral certification)")


if __name__ == "__main__":
    main()
