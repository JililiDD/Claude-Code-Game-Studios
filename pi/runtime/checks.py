#!/usr/bin/env python3
"""Invoke compatible CCGS validation hooks against a separate game project.

The original scripts receive their normal Claude-shaped JSON input, but the
paths and cwd are explicitly the Pi game root. This CLI never runs a commit,
push or write; it checks a proposed command or an already-written asset.
"""

import argparse
import json
import os
import subprocess
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = {
    "commit": "validate-commit.sh",
    "push": "validate-push.sh",
    "assets": "validate-assets.sh",
}


def validate(project: Path, kind: str, *, command: str = "", file: str = "") -> subprocess.CompletedProcess:
    root = project.resolve(strict=True)
    if not root.is_dir() or root == PACKAGE_ROOT or PACKAGE_ROOT in root.parents:
        raise ValueError("Choose a game directory outside the framework checkout")
    if not (root / "project.yaml").is_file():
        raise ValueError("Game lacks project.yaml")
    if kind not in SCRIPTS:
        raise ValueError(f"Unknown validation kind: {kind}")
    if kind == "assets":
        if not file:
            raise ValueError("Asset validation needs --file")
        location = (root / file).resolve()
        if not location.is_relative_to(root) or not location.is_file():
            raise ValueError("Asset must be a file inside the game")
        payload = {"tool_name": "Write", "tool_input": {"file_path": str(location)}}
    else:
        if not command:
            raise ValueError(f"{kind} validation needs --command")
        payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(root)}
    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.run(["bash", str(PACKAGE_ROOT / ".claude/hooks" / SCRIPTS[kind])],
                          input=json.dumps(payload), cwd=root, env=env, text=True,
                          capture_output=True, check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--kind", choices=tuple(SCRIPTS), required=True)
    parser.add_argument("--command", default="")
    parser.add_argument("--file", default="")
    args = parser.parse_args()
    try:
        result = validate(args.project, args.kind, command=args.command, file=args.file)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Pi CCGS checks: {exc}\n")
    print(result.stdout, end="")
    print(result.stderr, end="", file=__import__("sys").stderr)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
