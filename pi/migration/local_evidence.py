#!/usr/bin/env python3
"""Attach *bounded offline evidence* to contracts without claiming release.

The checks are scoped: workflow command expansion is not domain execution,
mock model review is not quality assessment, and local engine routing is not a
native engine run. All resource states remain draft or inapplicable.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "pi/migration/contracts.json"

SKILLS = ["pi/tests/test_behavior_matrix.py", "pi/tests/test_workflow_fleet.py"]
ROLES = ["pi/tests/test_behavior_matrix.py", "pi/tests/test_role_fleet.py", "pi/tests/test_model_switch.py"]
HOOKS = {
    "yaml-helper.sh": ["pi/tests/test_config.py", "pi/tests/test_settings.py", "pi/tests/test_code_root.py"],
    "validate-assets.sh": ["pi/tests/test_checks.py"],
    "validate-commit.sh": ["pi/tests/test_checks.py"],
    "validate-push.sh": ["pi/tests/test_checks.py"],
    "session-start.sh": ["pi/tests/test_session.py"],
    "session-stop.sh": ["pi/tests/test_session.py"],
    "pre-compact.sh": ["pi/tests/test_session.py"],
    "post-compact.sh": ["pi/tests/test_session.py"],
    "detect-gaps.sh": ["pi/tests/test_session.py"],
    "log-agent.sh": ["pi/tests/test_role_fleet.py", "pi/tests/test_gate_fleet.py"],
    "log-agent-stop.sh": ["pi/tests/test_role_fleet.py", "pi/tests/test_gate_fleet.py"],
}
EXTRA = {
    "start": ["pi/tests/test_init_game.py", "pi/tests/test_local_lifecycle.py"],
    "help": ["pi/tests/test_artifacts.py", "pi/tests/test_stories.py"],
    "project-stage-detect": ["pi/tests/test_artifacts.py", "pi/tests/test_code_root.py"],
    "adopt": ["pi/tests/test_migrate.py"],
    "setup-engine": ["pi/tests/test_engine_paths.py", "pi/tests/test_godot_check.py"],
    "settings": ["pi/tests/test_settings.py"],
    "dev-story": ["pi/tests/test_godot_check.py", "pi/tests/test_checks.py"],
    "skill-test": ["pi/tests/test_behavior_matrix.py"],
}


def expected(registry):
    for kind in ("skills", "agents", "hooks", "rules"):
        for source, contract in registry[kind].items():
            if contract["state"] == "inapplicable":
                contract.pop("local_evidence", None)
                contract.pop("local_scope", None)
                continue
            if kind == "skills":
                name = Path(source).parent.name
                checks = SKILLS + EXTRA.get(name, [])
                scope = "Pi skill command expansion, references and available offline helpers; source-domain decisions and full game phases still need owner validation"
            elif kind == "agents":
                checks = ROLES
                scope = "49 fresh read-only role invocations on mock Pi model, not real specialist quality or artifact authorship"
            elif kind == "hooks":
                checks = HOOKS[Path(source).name]
                scope = "Local hook/extension event or script fixture; interactive TUI and release behavior not proven"
            else:
                checks = ["pi/tests/test_rules.py"]
                scope = "Named path-scoped rule is supplied before a matching game write and isolates framework paths"
            for item in checks:
                if not (ROOT / item).is_file():
                    raise FileNotFoundError(item)
            contract["local_evidence"] = checks
            contract["local_scope"] = scope
    return registry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    registry = json.loads(TARGET.read_text(encoding="utf-8"))
    changed = expected(json.loads(json.dumps(registry)))
    if args.check:
        if changed != registry:
            parser.exit(1, "Offline evidence matrix is stale; rerun local_evidence.py\n")
        print("Bounded offline evidence assigned; no resource marked verified")
    else:
        TARGET.write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Recorded per-resource offline evidence (NOT a release verdict)")


if __name__ == "__main__":
    main()
