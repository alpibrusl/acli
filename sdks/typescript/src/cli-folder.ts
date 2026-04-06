/** Generate and maintain the .cli/ reference folder per ACLI spec §1.3. */

import * as fs from 'node:fs';
import * as path from 'node:path';
import type { CommandTree } from './introspect.js';

/** Generate the .cli/ folder with all required files. */
export function generateCliFolder(
  tree: CommandTree,
  targetDir?: string,
): string {
  const root = path.join(targetDir ?? process.cwd(), '.cli');
  fs.mkdirSync(path.join(root, 'examples'), { recursive: true });
  fs.mkdirSync(path.join(root, 'schemas'), { recursive: true });

  // commands.json
  fs.writeFileSync(
    path.join(root, 'commands.json'),
    JSON.stringify(tree, null, 2) + '\n',
  );

  // README.md
  writeReadme(root, tree);

  // Example scripts
  writeExamples(root, tree);

  // changelog.md (create if missing)
  const changelog = path.join(root, 'changelog.md');
  if (!fs.existsSync(changelog)) {
    fs.writeFileSync(
      changelog,
      `# Changelog\n\n## ${tree.version}\n\n- Initial release\n`,
    );
  }

  return root;
}

/** Check whether .cli/commands.json is out of date. */
export function needsUpdate(tree: CommandTree, targetDir?: string): boolean {
  const root = path.join(targetDir ?? process.cwd(), '.cli');
  const commandsFile = path.join(root, 'commands.json');
  if (!fs.existsSync(commandsFile)) return true;
  try {
    const existing = JSON.parse(fs.readFileSync(commandsFile, 'utf-8'));
    return JSON.stringify(existing) !== JSON.stringify(tree);
  } catch {
    return true;
  }
}

function writeReadme(cliDir: string, tree: CommandTree): void {
  const lines = [
    `# ${tree.name}`,
    '',
    `Version: ${tree.version}`,
    `ACLI version: ${tree.acli_version}`,
    '',
    '## Commands',
    '',
  ];
  for (const cmd of tree.commands) {
    lines.push(`### ${cmd.name}`, '', cmd.description, '');
    if (cmd.idempotent !== undefined) {
      lines.push(`Idempotent: ${cmd.idempotent}`, '');
    }
  }
  fs.writeFileSync(path.join(cliDir, 'README.md'), lines.join('\n') + '\n');
}

function writeExamples(cliDir: string, tree: CommandTree): void {
  for (const cmd of tree.commands) {
    if (!cmd.examples?.length) continue;
    const lines = [
      '#!/usr/bin/env bash',
      `# Examples for: ${cmd.name}`,
      '',
    ];
    for (const ex of cmd.examples) {
      lines.push(`# ${ex.description}`, ex.invocation, '');
    }
    fs.writeFileSync(
      path.join(cliDir, 'examples', `${cmd.name}.sh`),
      lines.join('\n'),
    );
  }
}
