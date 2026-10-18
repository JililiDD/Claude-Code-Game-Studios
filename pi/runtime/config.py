#!/usr/bin/env python3
"""Resolve game config with the existing CCGS policy, from an explicit game root.

A Pi package checkout and a game directory must never be conflated. This
adapter reuses the Claude edition's tested config semantics without depending
on Claude Code's skill-shell preprocessing or project environment variables.
"""

import argparse
import os
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:  # fail closed instead of silently defaulting on malformed YAML
    yaml = None

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
HELPER = PACKAGE_ROOT / ".claude/hooks/yaml-helper.sh"
VALID_KEYS = {
    "rigor", "review_mode", "automation", "workflow", "docs.density",
    "story_granularity", "qa.level", "team.size", "project.stage",
    "automation_always_ask", "engine", "testing.strict",
    "performance.enforce", "cert_tier", "platform.cert_tier", "system_overrides",
}


def validate_yaml(path: Path) -> None:
    if not path.exists():
        return
    if yaml is None:
        raise RuntimeError("Pi CCGS requires PyYAML to validate game config; install python3-yaml")

    class UniqueLoader(yaml.SafeLoader):
        pass

    def mapping(loader, node):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node)
            if not isinstance(key, str):
                raise ValueError(f"{path}: YAML mapping keys must be strings")
            if key in result:
                raise ValueError(f"{path}: duplicate YAML key: {key}")
            result[key] = loader.construct_object(value_node)
        return result

    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    try:
        data = yaml.load(path.read_text(encoding="utf-8-sig"), Loader=UniqueLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: malformed YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a YAML mapping, not {type(data).__name__}")


def resolve(project: Path, keys: str = "") -> str:
    project = project.resolve(strict=True)
    if not project.is_dir():
        raise ValueError(f"Not a game directory: {project}")
    if project == PACKAGE_ROOT or PACKAGE_ROOT in project.parents:
        raise ValueError("The framework checkout is not a game project")
    if not (project / "project.yaml").is_file():
        raise ValueError(f"Missing {project / 'project.yaml'}; initialize the game first")
    validate_yaml(project / "project.yaml")
    validate_yaml(project / "project.local.yaml")
    if not HELPER.is_file():
        raise FileNotFoundError(f"Missing bundled config helper: {HELPER}")
    requested = [key.strip() for key in keys.split(",")] if keys else []
    unknown = set(requested) - VALID_KEYS
    if unknown:
        raise ValueError(f"Unsupported config keys: {', '.join(sorted(unknown))}")
    command = ["bash", str(HELPER), "resolve_config"]
    if requested:
        command.extend(["--keys", ",".join(requested)])
    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)
    result = subprocess.run(command, cwd=project, env=env, text=True, capture_output=True, check=True)
    if not requested:
        valid = result.stdout.startswith("=== CCGS Resolved Config ===")
    else:
        lines = result.stdout.splitlines()
        valid = all(any(line.startswith(f"{('platform.cert_tier' if key == 'cert_tier' else key)}:")
                        for line in lines) for key in requested)
        if len(requested) > 2:
            valid = valid and result.stdout.startswith("=== CCGS Config (") and "=== end ===" in result.stdout
    if not valid:
        raise RuntimeError(f"Unexpected config output: {result.stdout[:200]!r} {result.stderr[:200]!r}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True, help="absolute or relative game root")
    parser.add_argument("--keys", default="", help="optional comma-separated config keys")
    args = parser.parse_args()
    try:
        print(resolve(args.project, args.keys), end="")
    except (OSError, ValueError, subprocess.CalledProcessError, RuntimeError) as exc:
        parser.exit(1, f"Pi CCGS config: {exc}\n")


if __name__ == "__main__":
    main()
