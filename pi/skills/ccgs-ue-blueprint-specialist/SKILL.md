---
name: ccgs-ue-blueprint-specialist
description: "Blueprint architecture and Blueprint/C++ boundary — optimization, maintainable graphs. Prevents Blueprint spaghetti, enforces clean BP patterns."
---

# ue-blueprint-specialist — Pi role migration candidate (NOT verified or released)

This skill applies the CCGS `ue-blueprint-specialist` domain guidance with **Pi's currently
selected model**, not the hardcoded model in the Claude Code role. Resolve the
framework root from this skill directory via `../../..` and first read
`<framework-root>/pi/skills/ccgs-role/SKILL.md`. Then read
`<framework-root>/.claude/agents/ue-blueprint-specialist.md` **in full** and read its
`<framework-root>/CCGS Skill Testing Framework/agents/engine/unreal/ue-blueprint-specialist.md` scenario expectations before declaring it complete.
The source test spec is an obligation, NOT proof of a passing Pi test. Apply
its body under the Pi-specific rules in `ccgs-role`. Resolve all `.claude/` references
against the framework; game artifacts live in the current game root.

Label the result as a **single-session role pass**. For a fresh, independently
drafted role contribution use `ccgs_role_consult` with a brief and evidence;
its output is unsaved and the main session writes only after approval. For an
independent named director gate use `ccgs_gate_review`; if unavailable or
NOT ASSESSED, leave the gate open. Do not launch a subagent just because the
original role mentions one. Ask before writes as
required by the game's automation mode. This is a draft until its individual
role and workflow integrations have been verified.
