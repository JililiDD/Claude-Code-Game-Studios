#!/usr/bin/env python3
"""Run repeatable implementation checks for handoff, never certify release.

These tests use mock models and local fixtures. They cannot assert that a real
model follows every instruction, that an engine launched, or that a package can
be safely installed/updated/removed in the user's environment.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKS = [
    [sys.executable, "pi/migration/audit.py", "--check"],
    [sys.executable, "pi/migration/behavior_matrix.py", "--check"],
    [sys.executable, "pi/migration/local_evidence.py", "--check"],
    [sys.executable, "pi/migration/generate_candidates.py", "--check"],
    [sys.executable, "pi/migration/generate_roles.py", "--check"],
    [sys.executable, "pi/migration/contracts.py"],
    [sys.executable, "-m", "unittest", "discover", "-s", "pi/tests", "-v"],
    ["bash", "-n", *[str(p) for p in sorted((ROOT / ".claude/hooks").glob("*.sh"))],
     *[str(p) for p in sorted((ROOT / ".claude/scripts").glob("*.sh"))]],
    ["git", "diff", "--check"],
]


def main():
    for command in CHECKS:
        print("$ " + " ".join(command), flush=True)
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            raise SystemExit(result.returncode)
    print("LOCAL IMPLEMENTATION CHECKS PASSED; release/user acceptance still NOT VERIFIED")


if __name__ == "__main__":
    main()
