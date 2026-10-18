---
name: skill-test
description: Audit Pi CCGS skills and role ports against source contracts, specs and observed behavior. Use static, spec, category or audit modes; never treat source-only checks as Pi runtime proof.
---

# Skill test — Pi maintainer candidate (not released)

This command tests the **Pi adapter**, not an installed game's code. The
original `.claude/skills/skill-test/SKILL.md` and `CCGS Skill Testing
Framework/` are bundled read-only source specs. Pi skills use different
frontmatter and have no Claude `model:`, `allowed-tools:` or `context: fork`
contract. A Claude static/spec score must never be copied to the Pi registry.
The package is unreleased: do not claim a Pi workflow verified from a
source-only spec.

## Scope and modes

Resolve `<framework-root>` from three parents above this skill directory,
independent of the current game root. Never edit package or game files while
running a read-only check. Parse `static [name|all]`, `spec [name]`,
`category [name|all]`, or `audit`; missing argument means `audit`. Names must
be exact basename slugs; do not accept path traversal. Unknown mode/name is
an error, not an empty passing report. Read the appropriate source files in
full, including `references/` and linked rules; inspect the Pi adapter and
any tests/evidence. Give a denominator and list missing material explicitly.

### `static`

For each named Pi skill, check valid Pi frontmatter (`name`, `description`),
matching directory name, no pinned `model:` or Claude tool grants, target
source exists, generated-drift check passes (unless manually adapted),
referenced game/framework paths have clear owners, original `!` shell
preprocessing has a mapped explicit Pi command, and gate/failure/approval
requirements are not silently dropped. Inspect **all** reference files and
imported material; do not infer correctness from a short wrapper. Run:

- `python3 <framework-root>/pi/migration/audit.py --check`
- `python3 <framework-root>/pi/migration/generate_candidates.py --check`
- `python3 <framework-root>/pi/migration/generate_roles.py --check`
- `python3 <framework-root>/pi/migration/contracts.py`

Report per-check PASS, WARN, FAIL or NOT ASSESSED and preserve the distinction
between registry **coverage** and release certification. A source skill's
seven Claude-only frontmatter checks are not Pi's seven checks.

### `spec`

Find source assertions via `CCGS Skill Testing Framework/catalog.yaml` and
its `spec` path; if absent, say NOT ASSESSED, not PASS. Test each fixture's
expected behavior against the Pi-specific skill, extension/runtime helpers,
source references and actual captured test output. A source assertion that
requires a Claude-specific tool, model pin, `CLAUDE.md` import or agent writer
needs an explicit Pi equivalent and fresh evidence. If no equivalent exists,
mark FAIL or NOT ASSESSED with the missing capability. A textual claim or
static spec reasoning **cannot** prove model selection, independent review,
engine execution, state mutation or failure recovery. Record unsatisfied
assertions by ID and do not set a registry state to verified based on this
report alone.

### `category`

Read the source `quality-rubric.md` and relevant skill/agent category. Retain
rubric intent (e.g., gate width, review independence, blocked-path handling),
not Claude orchestration mechanisms. Inspect the Pi role tool and its test
results where the metric requires independence. If a rubric is missing or
unclear, mark NOT ASSESSED; don't treat an unrelated category as a pass.

### `audit`

Enumerate actual 74 `.claude/skills/*/SKILL.md`, 49 `.claude/agents/*.md`,
14 hooks and 13 rules, compare to Pi skills and
`pi/migration/contracts.json`, and run
`python3 <framework-root>/pi/migration/contracts.py --release`. List every
unverified or excluded item and its reason. A failing release command means
**NOT READY**. Do not enable package resources, invent evidence or overwrite
source results in `CCGS Skill Testing Framework/catalog.yaml`.

## Reporting and writes

For each check show paths, evidence commands, observed results, missing
runtime tests and a PASS/WARN/FAIL/NOT ASSESSED verdict. State precisely which
source semantics were changed for Pi. By default write **nothing**; after
showing a draft, a user may approve a report under their game's
`production/qa/` (game evidence) or the maintainer's framework checkout
`pi/evidence/` (package evidence). Never write into a cached installed package
or source catalog from a game project. Follow up with the failing skill or
missing test; do not report a clean release until the full gate passes.
