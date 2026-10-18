#!/usr/bin/env python3
"""Use the bundled v1 migration against a separate game with explicit consent.

--dry-run is the safe default. Migration and finalization are different writes
and need separate user approval; the CLI flag only records that the Pi session
obtained it, it is not a substitute for asking the user.
"""
import argparse
import os
import subprocess
from pathlib import Path

FRAMEWORK = Path(__file__).resolve().parents[2]
SCRIPT = FRAMEWORK / ".claude/scripts/migrate-v1-config.sh"


def migration(project: Path, mode: str = "dry-run", *, approved: bool = False) -> subprocess.CompletedProcess:
    root = project.resolve(strict=True)
    if not root.is_dir() or root == FRAMEWORK or FRAMEWORK in root.parents:
        raise ValueError("Choose a game outside the framework checkout")
    if mode not in ("dry-run", "migrate", "finalize"):
        raise ValueError("Unknown migration mode")
    if mode != "dry-run" and not approved:
        raise PermissionError(f"Get separate explicit user approval for {mode} first")
    for relative in ("project.yaml", "production", "production/stage.txt",
                     "production/review-mode.txt", "production/migration-report.md",
                     ".claude/docs/technical-preferences.md"):
        entry = root / relative
        if not entry.resolve().is_relative_to(root):
            raise ValueError(f"Game migration path escapes via symlink: {relative}")
    env = os.environ.copy()
    env["CCGS_GAME_ROOT"] = str(root)
    # Avoid dead Claude-only commands inside a game-owned migration report.
    # --approved marks a *separately confirmed* finalize operation, not consent
    # to perform it automatically after this migration call.
    env["CCGS_MIGRATION_LABEL"] = "Pi CCGS migration adapter"
    env["CCGS_MIGRATION_FINALIZE_CMD"] = (
        f'python3 "{Path(__file__).resolve()}" --project "{root}" --mode finalize --approved'
    )
    env["CCGS_SETTINGS_CMD"] = "/skill:settings"
    env["CCGS_START_CMD"] = "/skill:start"
    env.pop("CLAUDE_PROJECT_DIR", None)
    arguments = {"dry-run": ["--dry-run"], "migrate": [], "finalize": ["--finalize"]}[mode]
    return subprocess.run(["bash", str(SCRIPT), *arguments], cwd=root, env=env,
                          text=True, capture_output=True, timeout=30, check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--mode", choices=("dry-run", "migrate", "finalize"), default="dry-run")
    parser.add_argument("--approved", action="store_true")
    args = parser.parse_args()
    try:
        result = migration(args.project, args.mode, approved=args.approved)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"Pi CCGS migration: {exc}\n")
    print(result.stdout, end="")
    print(result.stderr, end="", file=__import__("sys").stderr)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
