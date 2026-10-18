#!/usr/bin/env python3
"""Stage bundled Godot parse checker in an approved game, or describe its command.

This never runs Godot. The engine launch and visual observation remain separate
user validation gates; a staged script is NOT engine execution evidence.
"""
import argparse
from pathlib import Path

try:
    from .config import PACKAGE_ROOT, resolve as resolve_config
except ImportError:  # directly invoked by a Pi skill
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from pi.runtime.config import PACKAGE_ROOT, resolve as resolve_config

SOURCE = PACKAGE_ROOT / ".claude/scripts/godot-parse-check.gd"
DESTINATION = Path("addons/ccgs_pi/godot_parse_check.gd")


def game_root(project):
    root = Path(project).resolve(strict=True)
    if not root.is_dir() or root == PACKAGE_ROOT or PACKAGE_ROOT in root.parents:
        raise ValueError("Choose a separate game root, not the framework checkout")
    engine = resolve_config(root, "engine")
    if "engine: Godot " not in engine:
        raise ValueError(f"This check requires engine.name: Godot, got {engine.strip()}")
    return root


def stage(project, *, approved=False):
    root = game_root(project)
    if not approved:
        raise PermissionError("Ask the user to approve writing addons/ccgs_pi/godot_parse_check.gd first")
    target = root / DESTINATION
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.parent.resolve() != target.parent or not target.parent.resolve().is_relative_to(root):
        raise ValueError("Refusing to follow a game symlink outside its root")
    content = SOURCE.read_bytes()
    if target.exists() or target.is_symlink():
        if target.is_symlink() or target.read_bytes() != content:
            raise FileExistsError("Game parse check already exists with different content; refuse overwrite")
        return target
    with target.open("xb") as output:
        output.write(content)
    return target


def command(project, paths):
    root = game_root(project)
    target = root / DESTINATION
    if not target.is_file() or target.is_symlink() or target.read_bytes() != SOURCE.read_bytes():
        raise FileNotFoundError("Stage approved parse checker before constructing the command")
    if not paths:
        raise ValueError("At least one game-relative .gd path is required")
    scripts = []
    for path in paths:
        if path.startswith("res://"):
            path = path.removeprefix("res://")
        if Path(path).is_absolute() or ".." in Path(path).parts or not path.endswith(".gd"):
            raise ValueError(f"Unsafe Godot script path: {path}")
        canonical = (root / path).resolve(strict=True)
        if not canonical.is_file() or not canonical.is_relative_to(root):
            raise ValueError(f"Godot script is outside game: {path}")
        scripts.append(f"res://{canonical.relative_to(root).as_posix()}")
    return ["godot", "--headless", "--path", str(root), "-s", f"res://{DESTINATION.as_posix()}", "--", *scripts]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stage", action="store_true")
    group.add_argument("--command", action="store_true")
    parser.add_argument("--approved", action="store_true")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    try:
        if args.stage:
            print(stage(args.project, approved=args.approved))
        else:
            print(" ".join(__import__("shlex").quote(s) for s in command(args.project, args.paths)))
    except (OSError, PermissionError, ValueError) as error:
        parser.exit(1, f"Pi CCGS Godot check: {error}\n")


if __name__ == "__main__":
    main()
