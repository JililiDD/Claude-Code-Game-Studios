import { access } from "node:fs/promises";
import { promisify } from "node:util";
import { execFile } from "node:child_process";
import { realpathSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const exec = promisify(execFile);
const FRAMEWORK = realpathSync(resolve(dirname(fileURLToPath(import.meta.url)), "../.."));
const SCRIPT = resolve(FRAMEWORK, "pi/runtime/session.py");

async function gameRoot(cwd: string): Promise<string | undefined> {
  const root = realpathSync(cwd);
  const rel = relative(FRAMEWORK, root);
  if (!rel || (!rel.startsWith(`..${sep}`) && rel !== ".." && !isAbsolute(rel))) return;
  try { await access(resolve(root, "project.yaml")); return root; } catch { return; }
}

async function lifecycle(root: string, action: string, sessionId: string) {
  const { stdout } = await exec("python3", [SCRIPT, "--project", root, "--action", action,
    "--session-id", sessionId], { cwd: root, timeout: 20000, maxBuffer: 32768 });
  return stdout.replaceAll("Claude Code Game Studios", "CCGS for Pi")
    .replaceAll("Run: /start", "Run: /skill:start")
    .replaceAll("Run: /project-stage-detect", "Run: /skill:project-stage-detect");
}

export default function (pi: ExtensionAPI) {
  let context = "";
  let currentRoot: string | undefined;
  const refresh = async (ctx: ExtensionContext) => {
    const root = await gameRoot(ctx.cwd);
    if (root === currentRoot && context) return;
    currentRoot = root;
    context = "";
    if (!root) return;
    try {
      const id = ctx.sessionManager.getSessionFile() ?? "";
      const [start, gaps] = await Promise.all([
        lifecycle(root, "start", id), lifecycle(root, "gaps", id),
      ]);
      context = `${start}\n${gaps}`.slice(0, 12000);
    } catch (error) {
      context = `CCGS session context could not be collected: ${String(error)}`;
      ctx.ui.notify(context, "warning");
    }
  };
  pi.on("session_start", async (_event, ctx) => { context = ""; await refresh(ctx); });
  pi.on("session_tree", async (_event, ctx) => { context = ""; await refresh(ctx); });
  pi.on("before_agent_start", async (event, ctx) => {
    await refresh(ctx);  // /start can initialize project.yaml mid-session.
    if (!currentRoot || !context) return;
    event.systemPromptOptions.sections.ccgs_session = `Game root: ${currentRoot}. Framework root: ${FRAMEWORK}.\n${context}`;
  });
  pi.on("agent_settled", async (_event, ctx) => {
    await refresh(ctx);
    if (!currentRoot) return;
    try { await lifecycle(currentRoot, "settled", ctx.sessionManager.getSessionFile() ?? ""); }
    catch (error) { ctx.ui.notify(`CCGS session archive failed: ${String(error)}`, "warning"); }
  });
  pi.on("session_before_compact", async (_event, ctx) => {
    if (!currentRoot) return;
    try { await lifecycle(currentRoot, "pre-compact", ctx.sessionManager.getSessionFile() ?? ""); }
    catch (error) { ctx.ui.notify(`CCGS pre-compact observation failed: ${String(error)}`, "warning"); }
  });
  pi.on("session_compact", async (_event, ctx) => {
    if (!currentRoot) return;
    try {
      await lifecycle(currentRoot, "post-compact", ctx.sessionManager.getSessionFile() ?? "");
      context = await lifecycle(currentRoot, "start", ctx.sessionManager.getSessionFile() ?? "");
    } catch (error) { ctx.ui.notify(`CCGS post-compact recovery failed: ${String(error)}`, "warning"); }
  });
}
