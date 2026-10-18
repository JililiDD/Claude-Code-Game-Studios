#!/usr/bin/env python3
"""Inspect and preflight CCGS game settings using the bundled schema policy.

Read-only by design: the invoking skill shows the diff, asks permission and
edits the game file. This module never edits package or game configuration.
"""
import argparse
import json
import os
import re
import subprocess
from functools import cache
from pathlib import Path

try:
    from .config import HELPER, PACKAGE_ROOT, validate_yaml
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from pi.runtime.config import HELPER, PACKAGE_ROOT, validate_yaml

EFFECTS = PACKAGE_ROOT / ".claude/docs/effects-map.md"
FAMILY = ("modes.rigor", "modes.workflow", "docs.density", "qa.level",
          "modes.story_granularity", "modes.review_mode", "team.size")
KEY = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*$")


def root_for(project):
    root = Path(project).resolve(strict=True)
    if not root.is_dir() or root == PACKAGE_ROOT or PACKAGE_ROOT in root.parents:
        raise ValueError("Choose a separate game root")
    if not (root / "project.yaml").is_file():
        raise ValueError("Game has no project.yaml; use /skill:start first")
    validate_yaml(root / "project.yaml")
    validate_yaml(root / "project.local.yaml")
    return root


def helper(root, statement, *args):
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(root)
    proc = subprocess.run(["bash", "-c", 'source "$1"; ' + statement, "_", str(HELPER), *args],
                          cwd=root, env=env, capture_output=True, text=True, timeout=15, check=False)
    return proc


@cache
def reserved():
    """Discover headings directly above RESERVED banners; no hardcoded dead keys."""
    lines = EFFECTS.read_text(encoding="utf-8").splitlines()
    result = set()
    for i, line in enumerate(lines):
        if not line.startswith("> ### RESERVED"):
            continue
        headings = [x.removeprefix("## ") for x in lines[max(0, i - 14):i] if x.startswith("## ")]
        if not headings:
            raise ValueError("Reserved setting has no heading in effects-map.md")
        result.update(part.strip() for part in headings[-1].split(" and "))
    return sorted(result)


def inspect(project, key):
    root = root_for(project)
    if not KEY.fullmatch(key):
        raise ValueError("Invalid dotted setting path")
    effective = helper(root, 'resolve_setting "$2"', key)
    if effective.returncode or "\t" not in effective.stdout:
        raise RuntimeError(f"Could not resolve {key}: {effective.stderr}")
    value, source = effective.stdout.rstrip("\r\n").split("\t", 1)
    local = helper(root, 'get_yaml_key "$3" "$2"', key, "project.local.yaml").stdout.strip()
    team = helper(root, 'get_yaml_key "$3" "$2"', key, "project.yaml").stdout.strip()
    allowed = helper(root, 'is_locally_overridable "$2"', key)
    if allowed.returncode not in (0, 1):
        raise RuntimeError(f"Could not inspect local scope: {allowed.stderr}")
    return {"key": key, "value": value, "source": source, "local_value": local,
            "team_value": team, "locally_overridable": allowed.returncode == 0,
            "reserved": key in reserved()}


def validate(project, key, value, *, local=False):
    root = root_for(project)
    if not KEY.fullmatch(key) or not value:
        raise ValueError("Setting path and value must be nonempty")
    if local and helper(root, 'is_locally_overridable "$2"', key).returncode != 0:
        raise ValueError(f"{key} cannot be locally overridden")
    valid = helper(root, 'validate_enum_value "$2" "$3"', key, value)
    if valid.returncode:
        raise ValueError(valid.stderr.strip() or f"Invalid setting: {key}={value}")
    current = inspect(root, key)
    return {"key": key, "proposed": value, "destination": "project.local.yaml" if local else "project.yaml",
            "current": current, "reserved_warning": current["reserved"],
            "shadowed_by_local": bool(current["local_value"] and not local)}


def schema_errors(project):
    root = root_for(project)
    errors = {}
    for name in ("project.yaml", "project.local.yaml"):
        if (root / name).is_file():
            result = helper(root, 'validate_yaml_enum "$2"', name)
            if result.returncode not in (0, 1):
                raise RuntimeError(f"Could not validate {name}: {result.stderr}")
            if result.returncode:
                errors[name] = result.stderr.strip().splitlines()
    return errors


def all_settings(project):
    root = root_for(project)
    keys = []
    def walk(data, prefix=""):
        for key, value in data.items():
            dotted = prefix + key
            if isinstance(value, dict):
                walk(value, dotted + ".")
            elif dotted not in keys:
                keys.append(dotted)
    import yaml
    for name in ("project.yaml", "project.local.yaml"):
        if (root / name).is_file():
            walk(yaml.safe_load((root / name).read_text(encoding="utf-8-sig")) or {})
    for key in FAMILY:
        if key not in keys:
            keys.append(key)
    return [inspect(root, key) for key in keys]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--action", choices=("show", "all", "validate"), required=True)
    parser.add_argument("--key", default="")
    parser.add_argument("--value", default="")
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "all":
            result = {"entries": all_settings(args.project), "schema_errors": schema_errors(args.project)}
        elif args.action == "show":
            result = inspect(args.project, args.key)
        else:
            result = validate(args.project, args.key, args.value, local=args.local)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Pi CCGS settings: {error}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
