---
name: ccgs-gate
description: Run a CCGS director or lead review gate using a fresh model request on Pi's currently selected model. Use for gate-check verdicts and role-based independent review.
---

# CCGS independent gate — migration candidate

Use `ccgs_gate_review` when registered. Its `gate` is the basename of one of
`<framework-root>/.claude/docs/director-gates/*.md`, e.g. `cd-pillars`.
Pass a complete unsaved draft in `context` and **game-relative** evidence paths
in `files` (maximum 12, each smaller than 70 KB). The tool reads a fresh,
read-only reviewer context with the current Pi model. It returns a typed gate
verdict and usage. Verify the gate's named inputs were supplied; NOT ASSESSED
means insufficient evidence, never approval. Do not modify artifacts on a
reviewer's behalf or treat a same-session role pass as this independent gate.

For an independently drafted non-gate role contribution, use
`ccgs_role_consult` instead; its result is an unsaved draft, not a gate verdict.
Several independent role consultations may be issued in parallel, but the
coordinator must inspect every result and write approved artifacts itself.

If the tool is unavailable, the review fails, or the gate returns NOT ASSESSED,
keep the gate open and name what is missing. Never forge a verdict.
