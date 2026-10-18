#!/usr/bin/env python3
"""Record adapter candidates without claiming their behavior has been verified."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "pi/migration/contracts.json"
HOOKS = {
    "yaml-helper.sh": "pi/runtime/config.py",
    "validate-assets.sh": "pi/extensions/studio-checks.ts",
    "validate-commit.sh": "pi/extensions/studio-checks.ts",
    "validate-push.sh": "pi/extensions/studio-checks.ts",
    "session-start.sh": "pi/extensions/studio-session.ts",
    "detect-gaps.sh": "pi/extensions/studio-session.ts",
    "session-stop.sh": "pi/extensions/studio-session.ts",
    "pre-compact.sh": "pi/extensions/studio-session.ts",
    "post-compact.sh": "pi/extensions/studio-session.ts",
    "log-agent.sh": "pi/extensions/studio-gates.ts",
    "log-agent-stop.sh": "pi/extensions/studio-gates.ts",
}
CLAUDE_ONLY = {
    "notify.sh": "Claude Windows PowerShell toast hook; Pi uses native ctx.ui.notify for warnings and decisions",
    "validate-skill-change.sh": "Game projects do not edit installed package skills; Pi migration tests validate package skill changes",
    "log-instructions.sh": "Optional Claude instruction-load diagnostic; Pi path rules have an explicit extension and tests",
}


def main():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    for source, contract in data["hooks"].items():
        name = Path(source).name
        destination = HOOKS.get(name)
        if destination and contract["state"] == "pending":
            contract.update(state="draft", target=destination,
                            note="Pi adapter exists; full behavior NOT yet verified")
        elif name in CLAUDE_ONLY and contract["state"] == "pending":
            contract.update(state="inapplicable", target=None, note=CLAUDE_ONLY[name])
    for source, contract in data["rules"].items():
        if contract["state"] == "pending":
            contract.update(state="draft", target="pi/extensions/studio-rules.ts",
                            note="Pi path-scoped rule loader candidate; behavior NOT yet verified")
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Adapter candidates assigned without verification")


if __name__ == "__main__":
    main()
