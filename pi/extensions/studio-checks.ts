import { spawn } from "node:child_process";
import { existsSync, realpathSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const FRAMEWORK = realpathSync(resolve(dirname(fileURLToPath(import.meta.url)), "../.."));
const CHECKER = resolve(FRAMEWORK, "pi/runtime/checks.py");

function gameRoot(cwd: string): string | undefined {
  const root = realpathSync(cwd);
  if (!existsSync(resolve(root, "project.yaml"))) return;
  const rel = relative(FRAMEWORK, root);
  if (!rel || (!rel.startsWith(`..${sep}`) && rel !== ".." && !isAbsolute(rel))) return;
  return root;
}

async function run(root: string, kind: "commit" | "push" | "assets", flag: string, value: string) {
  return new Promise<{ code: number; output: string }>((done, fail) => {
    const child = spawn("python3", [CHECKER, "--project", root, "--kind", kind, flag, value], {
      cwd: root, stdio: ["ignore", "pipe", "pipe"],
    });
    let output = "";
    const append = (data: Buffer) => { output += data.toString("utf8"); if (output.length > 32768) child.kill(); };
    child.stdout.on("data", append);
    child.stderr.on("data", append);
    const timer = setTimeout(() => child.kill(), 20000);
    child.once("error", (error) => { clearTimeout(timer); fail(error); });
    child.once("close", (code) => { clearTimeout(timer); done({ code: code ?? 1, output: output.slice(0, 32768) }); });
  });
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash" && event.toolName !== "powershell") return;
    const command = event.input.command;
    if (typeof command !== "string" || !/\bgit\b/i.test(command)) return;
    const root = gameRoot(ctx.cwd);
    if (!root) return;
    try {
      for (const kind of ["commit", "push"] as const) {
        const check = await run(root, kind, "--command", command);
        if (check.code !== 0) return { block: true, reason: check.output || `${kind} validation failed` };
        if (check.output.trim()) ctx.ui.notify(check.output.slice(0, 1000), "warning");
      }
    } catch (error) {
      return { block: true, reason: `CCGS git validation unavailable: ${String(error)}` };
    }
  });

  pi.on("tool_result", async (event, ctx) => {
    if ((event.toolName !== "write" && event.toolName !== "edit") || event.isError) return;
    const inputPath = event.input.path;
    if (typeof inputPath !== "string") return;
    const root = gameRoot(ctx.cwd);
    if (!root) return;
    const path = resolve(root, inputPath);
    const rel = relative(root, path);
    if (!rel || rel === ".." || rel.startsWith(`..${sep}`) || isAbsolute(rel)) return;
    if (!/^(assets|Assets|Content)\//.test(rel.split(sep).join("/"))) return;
    try {
      const check = await run(root, "assets", "--file", rel);
      if (!check.output.trim() && check.code === 0) return;
      const message = check.output || "Asset validation could not run";
      if (check.code !== 0) {
        return { content: [...event.content, { type: "text" as const, text: `CCGS asset validation failed AFTER the edit/write; fix the file now:\n${message}` }], isError: true };
      }
      return { content: [...event.content, { type: "text" as const, text: `CCGS asset warning:\n${message}` }] };
    } catch (error) {
      return { content: [...event.content, { type: "text" as const, text: `CCGS asset validation unavailable: ${String(error)}` }], isError: true };
    }
  });
}
