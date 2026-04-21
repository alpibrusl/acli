/** AcliApp — the main application wrapper, equivalent to Python's ACLIApp. */

import { Command } from 'commander';
import { generateCliFolder, needsUpdate } from './cli-folder.js';
import { AcliError } from './errors.js';
import { ExitCode } from './exit-codes.js';
import type { CommandInfo, CommandTree } from './introspect.js';
import { createCommandTree } from './introspect.js';
import {
  type OutputFormat,
  emit,
  errorEnvelope,
  successEnvelope,
} from './output.js';
import { generateSkill, type SkillOptions } from './skill.js';

export interface AcliCommandMeta {
  examples: [string, string][];
  idempotent: boolean | 'conditional';
  seeAlso?: string[];
}

/**
 * ACLI-compliant application wrapper around Commander.
 *
 * Auto-registers `introspect`, `version`, and `skill` commands.
 * Auto-injects `--output` on all commands and `--dry-run` on
 * non-idempotent commands.
 */
export class AcliApp {
  readonly name: string;
  readonly version: string;
  private program: Command;
  private tree: CommandTree;
  private cliDir?: string;
  private skillOptions: SkillOptions;

  constructor(
    name: string,
    version: string,
    options?: {
      cliDir?: string;
      skillDescription?: string;
      skillWhenToUse?: string;
    },
  ) {
    this.name = name;
    this.version = version;
    this.cliDir = options?.cliDir;
    this.skillOptions = {
      description: options?.skillDescription,
      whenToUse: options?.skillWhenToUse,
    };
    this.tree = createCommandTree(name, version);

    this.program = new Command(name)
      .version(version)
      .description(`${name} v${version}`);

    this.registerIntrospect();
    this.registerVersion();
    this.registerSkill();
  }

  /**
   * Add a command with ACLI metadata.
   *
   * Auto-injects `--output` and `--dry-run` (if idempotent is false).
   */
  command(
    name: string,
    description: string,
    meta: AcliCommandMeta,
    handler: (opts: Record<string, unknown>) => void | Promise<void>,
  ): this {
    const cmd = this.program
      .command(name)
      .description(description)
      .option('--output <format>', 'Output format. type:enum[text|json|table]', 'text');

    if (meta.idempotent === false) {
      cmd.option('--dry-run', 'Describe actions without executing. type:bool', false);
    }

    cmd.action(async (opts: Record<string, unknown>) => {
      try {
        await handler(opts);
      } catch (err) {
        if (err instanceof AcliError) {
          process.exitCode = this.handleError(err);
        } else {
          const error = err instanceof Error ? err : new Error(String(err));
          process.exitCode = this.handleUnexpectedError(error);
        }
      }
    });

    // Build CommandInfo for introspection
    const info: CommandInfo = {
      name,
      description,
      arguments: [],
      options: [
        { name: 'output', type: 'OutputFormat', description: 'Output format. type:enum[text|json|table]', default: 'text' },
      ],
      subcommands: [],
      idempotent: meta.idempotent,
      examples: meta.examples.map(([d, i]) => ({ description: d, invocation: i })),
    };

    if (meta.idempotent === false) {
      info.options.push({
        name: 'dry_run', type: 'bool',
        description: 'Describe actions without executing. type:bool', default: false,
      });
    }

    if (meta.seeAlso?.length) {
      info.see_also = meta.seeAlso;
    }

    this.tree.commands.push(info);
    return this;
  }

  /** Add options to the last registered command (chain after .command()). */
  option(flags: string, description: string, defaultValue?: unknown): this {
    const cmds = this.program.commands;
    const lastCmd = cmds[cmds.length - 1];
    if (lastCmd) {
      lastCmd.option(flags, description, defaultValue as string | boolean | undefined);

      // Also add to introspect tree
      const lastInfo = this.tree.commands[this.tree.commands.length - 1];
      if (lastInfo) {
        const name = flags.replace(/^--/, '').split(/[\s,<]/)[0].replace(/-/g, '_');
        lastInfo.options.push({
          name,
          type: 'string',
          description,
          default: defaultValue,
        });
      }
    }
    return this;
  }

  /** Get the command tree. */
  commandTree(): CommandTree {
    return this.tree;
  }

  /** Run the application (parses argv). Returns exit code. */
  async run(argv?: string[]): Promise<ExitCode> {
    try {
      await this.program.parseAsync(argv ?? process.argv);
      return ExitCode.Success;
    } catch (err) {
      if (err instanceof AcliError) {
        return this.handleError(err);
      }
      return this.handleUnexpectedError(err instanceof Error ? err : new Error(String(err)));
    }
  }

  // ── Built-in commands ──────────────────────────────────────────────────

  private registerIntrospect(): void {
    this.program
      .command('introspect')
      .description('Output the full command tree as JSON for agent consumption.')
      .option('--acli-version', 'Show only the ACLI spec version', false)
      .option('--output <format>', 'Output format', 'json')
      .action((opts: { acliVersion?: boolean; output: string }) => {
        if (opts.acliVersion) {
          if (opts.output === 'json') {
            process.stdout.write(JSON.stringify({ acli_version: '0.1.0' }) + '\n');
          } else {
            process.stdout.write('acli 0.1.0\n');
          }
          return;
        }

        if (needsUpdate(this.tree, this.cliDir)) {
          generateCliFolder(this.tree, this.cliDir);
        }

        const envelope = successEnvelope('introspect', this.tree, this.version);
        emit(envelope, opts.output as OutputFormat);
      });
  }

  private registerVersion(): void {
    this.program
      .command('version')
      .description('Show version information.')
      .option('--output <format>', 'Output format', 'text')
      .action((opts: { output: string }) => {
        if (opts.output === 'json') {
          const data = { tool: this.name, version: this.version, acli_version: '0.1.0' };
          const envelope = successEnvelope('version', data, this.version);
          emit(envelope, 'json');
        } else {
          process.stdout.write(`${this.name} ${this.version}\n`);
          process.stdout.write('acli 0.1.0\n');
        }

        if (needsUpdate(this.tree, this.cliDir)) {
          generateCliFolder(this.tree, this.cliDir);
        }
      });
  }

  private registerSkill(): void {
    this.program
      .command('skill')
      .description('Generate a SKILL.md (agentskills.io) file for agent bootstrapping.')
      .option('--out <path>', 'Write skill file to this path instead of stdout')
      .option('--output <format>', 'Output format', 'text')
      .action((opts: { out?: string; output: string }) => {
        const content = generateSkill(this.tree, opts.out, this.skillOptions);

        if (opts.output === 'json') {
          const data = { path: opts.out ?? null, content };
          const envelope = successEnvelope('skill', data, this.version);
          emit(envelope, 'json');
        } else if (opts.out) {
          process.stdout.write(`Skill file written to ${opts.out}\n`);
        } else {
          process.stdout.write(content);
        }
      });
  }

  // ── Error handling ─────────────────────────────────────────────────────

  /** Handle an AcliError — emit JSON error envelope and return exit code. */
  handleError(err: AcliError): ExitCode {
    const cmdName = err.command ?? this.name;
    const envelope = errorEnvelope(cmdName, err.code, err.message, {
      hint: err.hint,
      docs: err.docs,
      version: this.version,
    });
    emit(envelope, 'json');
    return err.code;
  }

  private handleUnexpectedError(err: Error): ExitCode {
    const envelope = errorEnvelope(this.name, ExitCode.GeneralError, err.message, {
      hint: 'This is an unexpected error. Please report it.',
      version: this.version,
    });
    emit(envelope, 'json');
    return ExitCode.GeneralError;
  }
}
