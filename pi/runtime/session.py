#!/usr/bin/env python3
"""Run CCGS lifecycle observations/archives in a separate Pi game directory."""

import argparse
import os
import subprocess
from pathlib import Path

FRAMEWORK = Path(__file__).resolve().parents[2]
HOOKS = {"start": "session-start.sh", "gaps": "detect-gaps.sh",
         "settled": "session-stop.sh", "pre-compact": "pre-compact.sh",
         "post-compact": "post-compact.sh"}


def lifecycle(project: Path, action: str, session_id: str = "") -> subprocess.CompletedProcess:
    root = project.resolve(strict=True)
    if not root.is_dir() or root == FRAMEWORK or FRAMEWORK in root.parents:
        raise ValueError("Choose a game directory outside the framework checkout")
    if action not in HOOKS:
        raise ValueError(f"Unknown lifecycle action: {action}")
    if not (root / "project.yaml").is_file():
        raise ValueError("Game lacks project.yaml")
    env = os.environ.copy()
    env["CCGS_HELPER"] = str(FRAMEWORK / ".claude/hooks/yaml-helper.sh")
    env["CCGS_INTERFACE"] = "pi"
    env["CLAUDE_PROJECT_DIR"] = str(root)  # compatibility with the original hooks
    payload = '{"session_id":' + __import__("json").dumps(Path(session_id).name if session_id else "") + "}\n"
    return subprocess.run(["bash", str(FRAMEWORK / ".claude/hooks" / HOOKS[action])],
                          input=payload, cwd=root, env=env, capture_output=True,
                          text=True, timeout=15, check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--action", choices=tuple(HOOKS), required=True)
    parser.add_argument("--session-id", default="")
    args = parser.parse_args()
    try:
        result = lifecycle(args.project, args.action, args.session_id)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"Pi CCGS session: {exc}\n")
    print(result.stdout, end="")
    print(result.stderr, end="", file=__import__("sys").stderr)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
