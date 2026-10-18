#!/usr/bin/env python3
"""Create CCGS config in a *separate* game directory, after user approval.

Only fresh games are supported here; adopting an existing config is a distinct
workflow and must not be implemented by overwriting the user's files.
"""

import argparse
import re
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]

STAGES = ("Concept", "Systems Design", "Technical Setup")
RIGOR = ("minimal", "standard", "full")
AUTOMATION = ("collaborative", "guided", "autonomous")


def initialize(project: Path, stage: str, rigor: str, automation: str) -> None:
    if stage not in STAGES or rigor not in RIGOR or automation not in AUTOMATION:
        raise ValueError("Invalid stage, rigor or automation choice")
    root = project.resolve(strict=True)
    if not root.is_dir() or root == PACKAGE_ROOT or PACKAGE_ROOT in root.parents:
        raise ValueError("Choose a game directory outside the framework checkout")
    config = root / "project.yaml"
    mirror = root / "production/stage.txt"
    if config.exists() or mirror.exists():
        raise FileExistsError("Game configuration already exists; do not overwrite it")
    framework = (PACKAGE_ROOT / "project.yaml").read_text(encoding="utf-8")
    version = re.search(r"(?m)^  version: (\S+)$", framework)
    date = re.search(r"(?m)^  last_upgraded: (\S+)$", framework)
    if not version or not date:
        raise ValueError("Bundled framework metadata is missing")
    content = (
        "# CCGS game configuration; edit this project, not the installed framework.\n"
        "schema_version: 1\n\n"
        f"framework:\n  version: {version.group(1)}\n  last_upgraded: {date.group(1)}\n\n"
        f"project:\n  stage: {stage}\n\n"
        f"modes:\n  rigor: {rigor}\n  automation: {automation}\n"
    )
    # Refuse to clobber either destination. If the second exclusive create
    # fails, undo only the config file created by this call.
    with config.open("x", encoding="utf-8") as file:
        file.write(content)
    try:
        mirror.parent.mkdir(parents=True, exist_ok=True)
        with mirror.open("x", encoding="utf-8") as file:
            file.write(stage)
    except OSError:
        config.unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--rigor", choices=RIGOR, required=True)
    parser.add_argument("--automation", choices=AUTOMATION, required=True)
    args = parser.parse_args()
    try:
        initialize(args.project, args.stage, args.rigor, args.automation)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Pi CCGS init: {exc}\n")
    print(f"Initialized {args.project.resolve() / 'project.yaml'}")


if __name__ == "__main__":
    main()
