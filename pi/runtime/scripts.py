#!/usr/bin/env python3
"""Run observation-only CCGS scripts against an explicit separate game root.

No migration/finalization script is exposed here: those may edit/delete files
and require a dedicated approval and migration test path.
"""

import argparse
import os
import subprocess
from pathlib import Path

FRAMEWORK = Path(__file__).resolve().parents[2]
OBSERVATIONS = {
    "gdd-structure-check": "gdd-structure-check.sh",
    "project-coherence": "project-coherence.sh",
    "review-scope": "review-scope.sh",
    "review-receipts": "review-receipts.sh",
    "adr-dep-graph": "adr-dep-graph.sh",
}


def observe(project: Path, name: str, args=()) -> subprocess.CompletedProcess:
    root = project.resolve(strict=True)
    if not root.is_dir() or root == FRAMEWORK or FRAMEWORK in root.parents:
        raise ValueError("Choose a game directory outside the framework checkout")
    if name not in OBSERVATIONS:
        raise ValueError(f"Not an allowed observation script: {name}")
    if any(arg.startswith("-") or ".." in Path(arg).parts or Path(arg).is_absolute() for arg in args):
        raise ValueError("Script arguments must be game-relative paths or subcommands")
    for arg in args:
        # Subcommands and optional missing files are both legitimate; existing
        # symlink paths must not read outside the selected game.
        if not (root / arg).resolve().is_relative_to(root):
            raise ValueError(f"Script path escapes game root: {arg}")
    if name == "adr-dep-graph" and not args:
        args = ("docs/architecture",)
    env = os.environ.copy()
    env["CCGS_GAME_ROOT"] = str(root)
    env.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.run(["bash", str(FRAMEWORK / ".claude/scripts" / OBSERVATIONS[name]), *args],
                          cwd=root, env=env, capture_output=True, text=True, timeout=60, check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--name", choices=tuple(OBSERVATIONS), required=True)
    parser.add_argument("args", nargs="*")
    options = parser.parse_args()
    try:
        result = observe(options.project, options.name, options.args)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"Pi CCGS scripts: {exc}\n")
    print(result.stdout, end="")
    print(result.stderr, end="", file=__import__("sys").stderr)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
