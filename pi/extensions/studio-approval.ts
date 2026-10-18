import { existsSync, realpathSync } from "node:fs";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const exec = promisify(execFile);
const FRAMEWORK = realpathSync(resolve(dirname(fileURLToPath(import.meta.url)), "../.."));
const CONFIG = resolve(FRAMEWORK, "pi/runtime/config.py");

function gameRoot(cwd: string): string | undefined {
  const root = realpathSync(cwd);
  const rel = relative(FRAMEWORK, root);
  if (!rel || (rel !== ".." && !rel.startsWith(`..${sep}`) && !isAbsolute(rel))) return;
  return root;
}

async function mode(root: string): Promise<{ automation: string; always: string[] }> {
  if (!existsSync(resolve(root, "project.yaml"))) return { automation: "collaborative", always: [] };
  const { stdout } = await exec("python3", [CONFIG, "--project", root,
    "--keys", "automation,automation_always_ask"], { cwd: root, timeout: 15000, maxBuffer: 8192 });
  const automation = stdout.match(/^automation: (collaborative|guided|autonomous) \(/m)?.[1];
  const always = stdout.match(/^automation_always_ask: (.*) \((?:configured|default)\)$/m)?.[1];
  if (!automation || !always || /^notes:/m.test(stdout)) {
    throw new Error("CCGS approval mode could not be safely resolved");
  }
  return { automation, always: always.split(/,\s*/).map((value) => value.trim()) };
}

function inside(root: string, path: string): boolean {
  const rel = relative(root, resolve(root, path));
  return !!rel && rel !== ".." && !rel.startsWith(`..${sep}`) && !isAbsolute(rel);
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    const root = gameRoot(ctx.cwd);
    if (!root) return;
    const input = event.input;
    if (event.toolName === "bash" || event.toolName === "powershell") {
      const command = input.command;
      if (typeof command !== "string") return;
      const sensitive = /\b(?:git\b[\s\S]{0,200}\b(?:commit|push)\b|rm\s|rmdir\s|init_game\.py|migrate-v1-config\.sh)\b/i;
      if (!sensitive.test(command)) return;
      const accepted = await ctx.ui.confirm("CCGS sensitive command", `Approve this command in ${root}?\n${command.slice(0, 3000)}`);
      if (!accepted) return { block: true, reason: "CCGS sensitive command was not approved" };
      return;
    }
    if (event.toolName !== "write" && event.toolName !== "edit") return;
    const path = input.path;
    if (typeof path !== "string" || !inside(root, path)) return;
    try {
      const setting = await mode(root);
      const rel = relative(root, resolve(root, path)).split(sep).join("/");
      const newFile = !existsSync(resolve(root, path));
      const schema = rel === "project.yaml" || /(^|\/)(?:story|adr|gdd|control-manifest)[^/]*template[^/]*$/i.test(rel);
      const required = setting.automation === "collaborative"
        || (setting.automation === "guided" && newFile)
        || (schema && setting.always.includes("schema_changes"));
      if (!required) return;
      const preview = event.toolName === "write" ? input.content : `${input.oldText ?? ""}\n→\n${input.newText ?? ""}`;
      const accepted = await ctx.ui.confirm("CCGS game file approval",
        `May I ${newFile ? "create" : "update"} ${rel}?\n${String(preview ?? "").slice(0, 1600)}\n${String(preview ?? "").length > 1600 ? "[truncated — inspect full draft first]" : ""}`);
      if (!accepted) return { block: true, reason: `Write to ${rel} was not approved; wait for an explicit user decision` };
    } catch (error) {
      return { block: true, reason: `CCGS approval failed closed: ${String(error)}` };
    }
  });
}
