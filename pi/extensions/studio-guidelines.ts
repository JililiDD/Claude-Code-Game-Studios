import { existsSync, readFileSync, realpathSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const FRAMEWORK = realpathSync(resolve(dirname(fileURLToPath(import.meta.url)), "../.."));
const STANDARDS = readFileSync(resolve(FRAMEWORK, ".claude/docs/coding-standards.md"), "utf8");
const LAYOUT = readFileSync(resolve(FRAMEWORK, ".claude/docs/directory-structure.md"), "utf8");

function isGame(cwd: string): boolean {
  const root = realpathSync(cwd);
  const rel = relative(FRAMEWORK, root);
  return existsSync(resolve(root, "project.yaml")) && !!rel
    && (rel === ".." || rel.startsWith(`..${sep}`) || isAbsolute(rel));
}

export default function (pi: ExtensionAPI) {
  pi.on("before_agent_start", (event, ctx) => {
    if (!isGame(ctx.cwd)) return;
    event.systemPromptOptions.sections.ccgs_guidelines = `CCGS for Pi is a shared game-development framework installed at ${FRAMEWORK}. The current working directory ${ctx.cwd} is the writable game project. Read framework assets under ${FRAMEWORK}/.claude/; write game artifacts ONLY under the game project. Never interpret the framework checkout's CLAUDE.md as game-local directions. Use Pi's currently selected model; any Claude model pins in legacy files are inapplicable.\n\nCollaboration: Ask for project-shaping decisions and before writing files in collaborative mode. The studio-approval extension additionally checks direct write/edit calls, but cannot prove an entire multi-file draft was presented, or sandbox arbitrary shell commands; you must honor the full file-level and phase approval contract. Show the draft and destination, obtain an answer, and do not treat silence as consent. In guided/autonomous modes still stop for scope changes, deletion and schema changes, respecting the game's resolved automation setting. Never commit or push without the user's request.\n\nRole coordination: Leadership → department lead → specialist for complex cross-domain calls. Use ccgs_role_consult for fresh read-only role drafts; several independent consultations may run in parallel. They never write game files. Use ccgs_gate_review with complete game evidence for a named director gate. Do not claim a gate passed when NOT ASSESSED, blocked or not actually run. Resolve disagreements through the appropriate domain director and user.\n\nWhen implementing: Load game project.yaml via ${FRAMEWORK}/pi/runtime/config.py. Game docs/technical-preferences.md is the optional legacy fallback; never edit the framework's .claude/docs/technical-preferences.md. Check engine name/version and game-owned engine reference before using engine APIs. For any visible change, launch/observe the game and retain screenshot evidence before closing its story; a parse check is not a run. Read the matching path-scoped rule supplied by the Pi rules extension.\n\nFramework coding standards (references to .claude/ below resolve under ${FRAMEWORK}, not the game):\n${STANDARDS}\n\nFramework directory conventions:\n${LAYOUT}`;
  });
}
