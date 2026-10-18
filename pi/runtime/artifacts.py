#!/usr/bin/env python3
"""Evaluate package workflow catalog against an explicit Pi game directory."""

import argparse
import os
import subprocess
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PACKAGE_ROOT / ".claude/scripts/artifact-check.sh"
CATALOG = PACKAGE_ROOT / ".claude/docs/workflow-catalog.yaml"


def check(project: Path, *, phase: str = "", path: str = "", all_phases: bool = False) -> str:
    root = project.resolve(strict=True)
    if not root.is_dir() or root == PACKAGE_ROOT or PACKAGE_ROOT in root.parents:
        raise ValueError("Choose a game directory outside the framework checkout")
    if sum((bool(phase), bool(path), all_phases)) != 1:
        raise ValueError("Exactly one --phase, --path or --all is required")
    if not SCRIPT.is_file() or not CATALOG.is_file():
        raise FileNotFoundError("Missing bundled artifact checker or workflow catalog")
    command = ["bash", str(SCRIPT)]
    if not all_phases:
        command.extend(["--phase" if phase else "--path", phase or path])
    command.append(str(root))
    env = os.environ.copy()
    env["CCGS_CATALOG"] = str(CATALOG)
    result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, check=True)
    catalog_display = os.path.relpath(CATALOG, root).replace(os.sep, "/")
    if f"ROOT: {root}" not in result.stdout or f"CATALOG: {catalog_display}" not in result.stdout:
        raise RuntimeError(f"Unexpected artifact checker output: {result.stdout[:200]!r}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--phase", default="")
    selector.add_argument("--path", default="")
    selector.add_argument("--all", action="store_true", dest="all_phases")
    args = parser.parse_args()
    try:
        print(check(args.project, phase=args.phase, path=args.path, all_phases=args.all_phases), end="")
    except (OSError, ValueError, subprocess.CalledProcessError, RuntimeError) as exc:
        parser.exit(1, f"Pi CCGS artifacts: {exc}\n")


if __name__ == "__main__":
    main()
