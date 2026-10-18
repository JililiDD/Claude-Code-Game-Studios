import { existsSync, readFileSync, readdirSync, realpathSync } from "node:fs";
import { dirname, isAbsolute, matchesGlob, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const FRAMEWORK = realpathSync(resolve(dirname(fileURLToPath(import.meta.url)), "../.."));
const RULES = resolve(FRAMEWORK, ".claude/rules");
const rules = readdirSync(RULES).filter((name) => name.endsWith(".md")).sort().map((name) => {
  const source = readFileSync(resolve(RULES, name), "utf8");
  const front = source.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!front) throw new Error(`Rule missing frontmatter: ${name}`);
  const paths = [...front[1].matchAll(/^\s*-\s*"([^"]+)"\s*$/gm)].map((match) => match[1]);
  if (!paths.length) throw new Error(`Rule missing path patterns: ${name}`);
  return { name, paths, body: source.slice(front[0].length) };
});

function inGame(cwd: string, path: string): string | null {
  const root = realpathSync(cwd);
  if (!existsSync(resolve(root, "project.yaml"))) return null;
  const frameworkRel = relative(FRAMEWORK, root);
  if (!frameworkRel || (frameworkRel !== ".." && !frameworkRel.startsWith(`..${sep}`) && !isAbsolute(frameworkRel))) {
    return null;
  }
  const full = resolve(root, path);
  const rel = relative(root, full);
  if (!rel || rel === ".." || rel.startsWith(`..${sep}`) || isAbsolute(rel)) return null;
  return rel.split(sep).join("/");
}

function unsafeWrite(cwd: string, path: string): string | null {
  const root = realpathSync(cwd);
  const frameworkRel = relative(FRAMEWORK, root);
  if (!frameworkRel || (frameworkRel !== ".." && !frameworkRel.startsWith(`..${sep}`) && !isAbsolute(frameworkRel))) {
    return null; // A maintainer working in this checkout is not a game session.
  }
  const target = resolve(root, path);
  const rel = relative(root, target);
  if (!rel || rel === ".." || rel.startsWith(`..${sep}`) || isAbsolute(rel)) {
    return "CCGS game writes cannot target the framework or paths outside the game root";
  }
  let existing = target;
  while (!existsSync(existing) && existing !== root) existing = dirname(existing);
  const canonical = realpathSync(existing);
  const contained = relative(root, canonical);
  if (contained === ".." || contained.startsWith(`..${sep}`) || isAbsolute(contained)) {
    return "CCGS game writes cannot follow a symlink outside the game root";
  }
  return null;
}

export default function (pi: ExtensionAPI) {
  let supplied = new Set<string>();
  pi.on("before_agent_start", (event, ctx) => {
    if (event.messageType === "user") supplied = new Set();
    if (!inGame(ctx.cwd, "project.yaml")) return;
    const list = rules.map((rule) => `${rule.name}: ${rule.paths.join(", ")}`).join("\n");
    event.systemPromptOptions.sections.ccgs_rules = `CCGS path-scoped game rules are installed at ${RULES}. Before editing a matching path, follow its rule. A first edit may be blocked to show the full rule. Framework paths are never game paths.\n${list}`;
  });

  pi.on("tool_call", (event, ctx) => {
    if (event.toolName !== "edit" && event.toolName !== "write") return;
    const path = event.input.path;
    if (typeof path !== "string") return;
    const unsafe = unsafeWrite(ctx.cwd, path);
    if (unsafe) return { block: true, reason: unsafe };
    const file = inGame(ctx.cwd, path);
    if (!file) return;
    const matching = rules.filter((rule) => rule.paths.some((pattern) => matchesGlob(file, pattern)));
    const needed = matching.filter((rule) => !supplied.has(rule.name));
    if (!needed.length) return;
    for (const rule of needed) supplied.add(rule.name);
    return {
      block: true,
      reason: `CCGS rules for ${file} (review these instructions, then retry the edit/write):\n${needed.map((rule) => `## ${rule.name}\n${rule.body}`).join("\n")}`,
    };
  });
}
