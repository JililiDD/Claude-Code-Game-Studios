---
name: ccgs-role
description: Apply a Claude Code Game Studios specialist's domain guidance using Pi's currently selected model. Use for a named studio role; this is not a separate agent or independent review.
---

# CCGS role adapter — migration candidate

Find the framework root by resolving this SKILL.md's directory, then its
`../../..` ancestor. Run `python3 <framework-root>/pi/runtime/role.py --list`
when the requested role is unclear; run it with `--name <exact-role-name>` to
read the role's body. Only accept names returned by `--list`.

Apply domain responsibilities, quality checks, boundaries, escalation advice
and verdict formats from the role definition to the user's game project.
**Do not copy Claude Code runtime behavior** from that file:

- Ignore its frontmatter model, tool grant, memory and `skills:` fields. Stay
  on Pi's currently selected model and available tools.
- Treat `AskUserQuestion` as asking the user in conversation and waiting.
- `Agent` and `Task` are not Claude Code tools in Pi. Do not launch
  subagents on your own. A separately drafted role contribution uses the
  `ccgs_role_consult` extension with a bounded brief and game evidence; it
  returns an **unsaved draft** to the main Pi session for approval and writing.
  When a named director gate needs an independent verdict, pass complete
  evidence to `ccgs_gate_review` (see `/skill:ccgs-gate`). Both tools make
  fresh, read-only requests on Pi's current model. If the relevant tool is
  unavailable or its verdict is NOT ASSESSED, keep that gate open instead of
  inventing another agent's approval.
- A relative `.claude/` reference is a framework reference: resolve it under
  the installed package root, never under the game root unless the user
  explicitly configured an equivalent game-owned resource. `docs/`, `design/`,
  `production/`, `assets/`, and source paths in a role refer to the game root.
- Follow the user's selected automation/approval choices. Do not infer that
  the user's request to consult a role grants permission to edit files,
  delegate, commit or push.

Label the response as a **single-session role pass** so it cannot be mistaken
for an independent second-model assessment. If another workflow requires a
truly independent sign-off, that gate remains open until the separate review
is actually performed and its result inspected.
