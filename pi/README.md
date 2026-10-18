# CCGS for Pi — work in progress

This adapter is **not a complete release**. The root package manifest currently
exposes no Pi resources. Do not use it as a production game-development
workflow or describe its draft wrappers as migrated functionality. The
completion gate is `python3 pi/migration/contracts.py --release`; it must pass
before changing the manifest or publishing an installation command.

## Intended usage after release

1. Install the Pi package once from the maintained Git fork. A game does not
   clone the entire framework: its `project.yaml`, `design/`, source and
   `production/` live in its own repository.
2. Run Pi from that **game's root**. Select any configured Pi model using
   `/model` (or cycle with `Ctrl+P`). A model change does not change the CCGS
   workflow settings, which are owned by the game's `project.yaml`.
3. Use `/skill:start` for new projects, `/skill:project-stage-detect` for
   existing projects, and `/skill:help` for next-step guidance. A named role
   is `/skill:ccgs-<role>`. Fresh read-only role drafts use
   `ccgs_role_consult`; director verdicts use `ccgs_gate_review` with the
   current Pi model and explicit game evidence, not a Claude Code subagent.
   The guidelines and path rules extensions apply only to initialized games.
4. Do not run Pi in the framework's own repository as if it were a game. Pi
   can read `CLAUDE.md` context files; that root document is written for
   Claude Code and makes Claude-specific tool assumptions.

## Development and verification

- Python 3 with PyYAML (`python3-yaml`) is required to validate game YAML;
  malformed or duplicate-key configs are rejected rather than defaulted.
- `python3 pi/migration/local_check.py` runs model/engine-independent implementation checks and source drift checks. It does **not** certify real-model or engine behavior.
- `python3 -m unittest discover -s pi/tests -v`
- `python3 pi/migration/audit.py --check`
- `python3 pi/migration/behavior_matrix.py --check`
- `python3 pi/migration/local_evidence.py --check` (bounded test-file evidence; does not promote statuses)
- `python3 pi/migration/generate_candidates.py --check`
- `python3 pi/migration/generate_roles.py --check`
- `python3 pi/migration/contracts.py` (coverage of tracking records only)
- `python3 pi/migration/contracts.py --release` (must fail until every resource
  is verified, approved exclusions are justified, and package entry points
  are enabled)

The existing `.claude/` version remains the supported production route during
migration. See `pi/migration/README.md`, `pi/migration/contracts.json` and
`pi/USER-VALIDATION.md` for scope, current statuses and the owner's remaining
real-model, engine and packaging acceptance checklist.
