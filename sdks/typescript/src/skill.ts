/**
 * Generate SKILL.md files from ACLI command trees.
 *
 * Emits a file conforming to the agentskills.io open standard
 * (https://agentskills.io): YAML frontmatter (`name`, `description`, optional
 * `when_to_use`) followed by the ACLI command reference body.
 */

import * as fs from 'node:fs';
import * as path from 'node:path';
import type { CommandInfo, CommandTree } from './introspect.js';

const BUILTIN_COMMANDS = new Set(['introspect', 'version', 'skill']);

export interface SkillOptions {
  description?: string;
  whenToUse?: string;
}

function oneLine(value: string): string {
  return value.split(/\s+/).filter(Boolean).join(' ');
}

const YAML_RESERVED_START = new Set([
  '!', '&', '*', '?', '|', '>', '\'', '"', '%', '@', '`', '#', ',', '[', ']', '{', '}', '-', ':',
]);

/** Render a scalar safe for a single-line YAML block mapping value. */
function yamlScalar(value: string): string {
  if (value === '') return '""';
  const needsQuoting =
    value.includes(': ') ||
    value.includes(' #') ||
    YAML_RESERVED_START.has(value[0]) ||
    value.endsWith(':') ||
    value.trim() !== value;
  if (!needsQuoting) return value;
  const escaped = value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  return `"${escaped}"`;
}

function defaultDescription(name: string, userCommands: CommandInfo[]): string {
  if (userCommands.length === 0) return `Invoke the \`${name}\` CLI.`;
  const shown = userCommands.slice(0, 4).map(c => c.name);
  const suffix = userCommands.length > 4 ? '…' : '';
  return `Invoke the \`${name}\` CLI. Commands: ${shown.join(', ')}${suffix}`;
}

/** Generate a SKILL.md file from an ACLI command tree. */
export function generateSkill(
  tree: CommandTree,
  targetPath?: string,
  options: SkillOptions = {},
): string {
  const { name, version, commands } = tree;
  const userCommands = commands.filter(c => !BUILTIN_COMMANDS.has(c.name));
  const description = options.description
    ? oneLine(options.description)
    : defaultDescription(name, userCommands);

  const lines: string[] = [
    '---',
    `name: ${yamlScalar(name)}`,
    `description: ${yamlScalar(description)}`,
  ];
  if (options.whenToUse) lines.push(`when_to_use: ${yamlScalar(oneLine(options.whenToUse))}`);
  lines.push('---', '');

  lines.push(`# ${name}`, '');
  lines.push(`> Auto-generated skill file for \`${name}\` v${version}`);
  lines.push(`> Re-generate with: \`${name} skill\` or \`acli skill --bin ${name}\``);
  lines.push('');

  // Quick reference
  lines.push('## Available commands', '');
  for (const cmd of userCommands) {
    let tag = '';
    if (cmd.idempotent === true) tag = ' (idempotent)';
    else if (cmd.idempotent === 'conditional') tag = ' (conditionally idempotent)';
    lines.push(`- \`${name} ${cmd.name}\` — ${cmd.description}${tag}`);
  }
  lines.push('');

  // Detailed usage
  for (const cmd of userCommands) {
    lines.push(`## \`${name} ${cmd.name}\``, '');
    if (cmd.description) lines.push(cmd.description, '');

    if (cmd.options.length > 0) {
      lines.push('### Options', '');
      for (const opt of cmd.options) {
        const optName = opt.name.replace(/_/g, '-');
        const def = opt.default !== undefined ? ` [default: ${opt.default}]` : '';
        lines.push(`- \`--${optName}\` (${opt.type}) — ${opt.description}${def}`);
      }
      lines.push('');
    }

    if (cmd.arguments.length > 0) {
      lines.push('### Arguments', '');
      for (const arg of cmd.arguments) {
        const req = arg.required ? 'required' : 'optional';
        lines.push(`- \`${arg.name}\` (${arg.type}, ${req}) — ${arg.description}`);
      }
      lines.push('');
    }

    if (cmd.examples?.length) {
      lines.push('### Examples', '');
      for (const ex of cmd.examples) {
        lines.push('```bash', `# ${ex.description}`, ex.invocation, '```', '');
      }
    }

    if (cmd.see_also?.length) {
      const refs = cmd.see_also.map(s => `\`${name} ${s}\``).join(', ');
      lines.push(`**See also:** ${refs}`, '');
    }
  }

  // Output format
  lines.push('## Output format', '');
  lines.push(
    'All commands support `--output json|text|table`. When using `--output json`, ' +
    'responses follow a standard envelope:',
  );
  lines.push('', '```json');
  lines.push('{"ok": true, "command": "...", "data": {...}, "meta": {"duration_ms": ..., "version": "..."}}');
  lines.push('```', '');

  // Exit codes
  lines.push('## Exit codes', '');
  lines.push('| Code | Meaning | Action |');
  lines.push('|------|---------|--------|');
  lines.push('| 0 | Success | Proceed |');
  lines.push('| 2 | Invalid arguments | Correct and retry |');
  lines.push('| 3 | Not found | Check inputs |');
  lines.push('| 5 | Conflict | Resolve conflict |');
  lines.push('| 8 | Precondition failed | Fix precondition |');
  lines.push('| 9 | Dry-run completed | Review and confirm |');
  lines.push('');

  // Discovery
  lines.push('## Further discovery', '');
  lines.push(`- \`${name} --help\` — full help for any command`);
  lines.push(`- \`${name} introspect\` — machine-readable command tree (JSON)`);
  lines.push('- `.cli/README.md` — persistent reference (survives context resets)');
  lines.push('');

  const content = lines.join('\n');

  if (targetPath) {
    fs.mkdirSync(path.dirname(targetPath), { recursive: true });
    fs.writeFileSync(targetPath, content);
  }

  return content;
}
