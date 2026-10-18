#!/usr/bin/env python3
"""Read ordered game-story status via the shared CCGS checker."""

import argparse
import os
import subprocess
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PACKAGE_ROOT / ".claude/scripts/story-status.sh"


def status(project: Path) -> str:
    root = project.resolve(strict=True)
    if not root.is_dir() or root == PACKAGE_ROOT or PACKAGE_ROOT in root.parents:
        raise ValueError("Choose a game directory outside the framework checkout")
    env = os.environ.copy()
    env["CCGS_GAME_ROOT"] = str(root)
    result = subprocess.run(["bash", str(SCRIPT)], cwd=root, env=env,
                            text=True, capture_output=True, check=True)
    if not result.stdout.startswith(("STORIES", "IN_REVIEW", "IN_PROGRESS", "TODO", "BLOCKED", "OTHER", "NO_STATUS", "COMPLETE")):
        raise RuntimeError(f"Unexpected story checker output: {result.stdout[:200]!r}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(status(args.project), end="")
    except (OSError, ValueError, subprocess.CalledProcessError, RuntimeError) as exc:
        parser.exit(1, f"Pi CCGS stories: {exc}\n")


if __name__ == "__main__":
    main()
