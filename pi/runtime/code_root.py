#!/usr/bin/env python3
"""Resolve Godot/Unity/Unreal game source root using the shared CCGS policy."""
import argparse
import os
import subprocess
from pathlib import Path

try:
    from .config import HELPER, PACKAGE_ROOT, validate_yaml
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from pi.runtime.config import HELPER, PACKAGE_ROOT, validate_yaml


def resolve(project):
    root = Path(project).resolve(strict=True)
    if not root.is_dir() or root == PACKAGE_ROOT or PACKAGE_ROOT in root.parents:
        raise ValueError("Choose an independent game directory")
    for name in ("project.yaml", "project.local.yaml"):
        validate_yaml(root / name)
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(root)
    # The original resolver is the authority for legacy preferences and for
    # case-exact detection on case-insensitive file systems.
    result = subprocess.run(["bash", "-c", 'source "$1"; resolve_code_root', "_", str(HELPER)],
                            cwd=root, env=env, capture_output=True, text=True, timeout=15, check=True)
    pieces = result.stdout.split("\t", 1)
    if len(pieces) != 2 or pieces[0] not in ("", "src", "Assets", "Source"):
        raise RuntimeError(f"Unexpected code-root resolver output: {result.stdout!r}")
    return pieces[0] or None, pieces[1].strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    try:
        path, source = resolve(args.project)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Pi CCGS code root: {error}\n")
    if not path:
        parser.exit(1, "NOT ASSESSED — code root unresolved; no source scan was performed\n")
    print(f"{path}\t{source}")


if __name__ == "__main__":
    main()
